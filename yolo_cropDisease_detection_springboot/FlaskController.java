import com.alibaba.fastjson2.JSON;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.client.ResourceAccessException;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.TimeUnit;

@RestController
@RequestMapping("/flask")
public class FlaskController {
    // 核心修改：统一Flask局域网地址（和Vue、Vite配置保持一致，唯一修改点）
    private static final String FLASK_BASE_URL = "http://192.168.0.101:5000";
    // 优化：配置RestTemplate，增加超时时间，避免请求卡死
    private final RestTemplate restTemplate;

    // 构造方法初始化RestTemplate，设置连接超时+读取超时（5秒）
    public FlaskController() {
        this.restTemplate = new RestTemplate();
        // 设置请求工厂，配置超时
        org.springframework.http.client.SimpleClientHttpRequestFactory factory =
                new org.springframework.http.client.SimpleClientHttpRequestFactory();
        factory.setConnectTimeout((int) TimeUnit.SECONDS.toMillis(5)); // 连接超时5秒
        factory.setReadTimeout((int) TimeUnit.SECONDS.toMillis(5));    // 读取响应超时5秒
        this.restTemplate.setRequestFactory(factory);
    }

    // 1. 获取模型列表接口 - 转发到Flask的/file_names
    @GetMapping("/file_names")
    public ResponseEntity<Map<String, Object>> getFileNames() {
        Map<String, Object> result = new HashMap<>(3);
        try {
            // 转发GET请求到Flask
            String flaskResponse = restTemplate.getForObject(FLASK_BASE_URL + "/file_names", String.class);
            // 自动解析Flask的JSON响应，前端无需二次解析
            Object data = JSON.parse(flaskResponse);
            result.put("code", 0);
            result.put("msg", "获取模型列表成功");
            result.put("data", data);
            return ResponseEntity.ok(result);
        } catch (ResourceAccessException e) {
            // 捕获Flask连接失败异常（Flask未启动/地址错误）
            result.put("code", -1);
            result.put("msg", "Flask服务未启动或地址错误，请检查：" + FLASK_BASE_URL);
            return ResponseEntity.status(HttpStatus.BAD_GATEWAY).body(result);
        } catch (Exception e) {
            // 其他异常捕获
            result.put("code", -1);
            result.put("msg", "获取模型列表失败：" + e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(result);
        }
    }

    // 2. 图像检测预测接口 - 转发到Flask的/predict
    @PostMapping("/predict")
    public ResponseEntity<Map<String, Object>> predict(@RequestBody Map<String, Object> params) {
        Map<String, Object> result = new HashMap<>(3);
        try {
            // 设置请求头，告诉Flask接收JSON数据
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Map<String, Object>> requestEntity = new HttpEntity<>(params, headers);
            
            // 转发POST请求到Flask
            String flaskResponse = restTemplate.postForObject(
                    FLASK_BASE_URL + "/predict",
                    requestEntity,
                    String.class
            );
            // 自动解析Flask的JSON响应，前端直接使用data即可
            Object data = JSON.parse(flaskResponse);
            result.put("code", 0);
            result.put("msg", "杂草检测成功");
            result.put("data", data);
            return ResponseEntity.ok(result);
        } catch (ResourceAccessException e) {
            // 精准捕获Flask连接异常，给前端明确提示
            result.put("code", -1);
            result.put("msg", "Flask服务未启动或地址错误，请检查：" + FLASK_BASE_URL);
            return ResponseEntity.status(HttpStatus.BAD_GATEWAY).body(result);
        } catch (Exception e) {
            result.put("code", -1);
            result.put("msg", "杂草检测失败：" + e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(result);
        }
    }
}
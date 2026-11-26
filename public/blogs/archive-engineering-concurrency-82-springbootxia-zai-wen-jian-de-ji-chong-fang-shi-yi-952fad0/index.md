# 第82节 SpringBoot下载文件的几种方式，一次性搞懂

# 1、前言
文件下载，常用的一个功能，比较简单
但是有可能会遇到一些问题
1. 文件太大，若写法上有问题，可能会导致内存溢出
2. 文件中文名称乱码问题
本文将给大家展示SpringBoot中下载文件常见的几种方式，顺便解决这些问题。
# 2、小文件下载
## 2.1、方式1：HttpServletResponse.write
代码如下，直接将文件一次性读取到内存中，然后通过response将文件内容输出到客户端，这种方式适合小文件，若文件比较大的时候，将文件一次性加载到内存中会导致OOM，这点需要注意
```java
@GetMapping("/download1")
public void download1(HttpServletResponse response) throws IOException {
    // 指定要下载的文件
    File file = ResourceUtils.getFile("classpath:文件1.txt");
    // 文件转成字节数组
    byte[] fileBytes = Files.readAllBytes(file.toPath());
    //文件名编码，防止中文乱码
    String filename = URLEncoder.encode(file.getName(), "UTF-8");
    // 设置响应头信息
    response.setHeader("Content-Disposition", "attachment; filename=\"" + filename + "\"");
    // 内容类型为通用类型，表示二进制数据流
    response.setContentType("application/octet-stream");
    //输出文件内容
    try (OutputStream os = response.getOutputStream()) {
        os.write(fileBytes);
    }
}
```
> 乱码的解决，主要靠下面这几行代码
>
> ```java
> //文件名编码，防止中文乱码
> String filename = URLEncoder.encode(file.getName(), "UTF-8");
> // 设置响应头信息
> response.setHeader("Content-Disposition", "attachment; filename=\"" + filename + "\"");
> ```
启动系统，看下效果，浏览器中访问：http://localhost:8080/download1
## 2.2、方式2：ResponseEntity&lt;byte[]&gt;
代码如下，方法需要返回`ResponseEntity`类型的对象，这个类是SpringBoot中自带的，是对http响应结果的一种封装，可以用来构建http响应结果：包含状态码、头、响应体等信息。
```java
@GetMapping("/download2")
public ResponseEntity<byte[]> download2() throws IOException {
    // 指定要下载的文件
    File file = ResourceUtils.getFile("classpath:文件1.txt");
    // 文件转成字节数组
    byte[] fileBytes = Files.readAllBytes(file.toPath());
    //文件名编码，防止中文乱码
    String filename = URLEncoder.encode(file.getName(), "UTF-8");
    //构建响应实体：ResponseEntity，ResponseEntity中包含了http请求的响应信息，比如状态码、头、body
    ResponseEntity<byte[]> responseEntity = ResponseEntity.ok()
            .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + filename + "\"")
            .header(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_OCTET_STREAM_VALUE)
            .body(fileBytes);
    return responseEntity;
}
```
看下效果，浏览器中访问：http://localhost:8080/download2
上面的2种方式，都是先将文件读取到字节数组，然后再返回给客户端，如果文件太大，将文件内容读取到内存，可能会导致oom。
所以，上面2种方式，大家了解就行了，不建议使用。
# 3、通用方案（适合任何大小文件），建议采用
## 2.1、方式1：边读取+边输出
```java
@GetMapping("/download3")
public void download3(HttpServletResponse response) throws IOException {
    // 指定要下载的文件
    File file = ResourceUtils.getFile("classpath:文件1.txt");
    //文件名编码，防止中文乱码
    String filename = URLEncoder.encode(file.getName(), "UTF-8");
    // 设置响应头信息
    response.setHeader("Content-Disposition", "attachment; filename=\"" + filename + "\"");
    // 内容类型为通用类型，表示二进制数据流
    response.setContentType("application/octet-stream");
    // 循环，边读取边输出，可避免大文件时OOM
    try (InputStream inputStream = new FileInputStream(file);
         OutputStream os = response.getOutputStream()) {
        byte[] bytes = new byte[1024];
        int readLength;
        while ((readLength = inputStream.read(bytes)) != -1) {
            os.write(bytes, 0, readLength);
        }
    }
}
```
看下效果，浏览器中访问：http://localhost:8080/download3
## 2.3、方式2：返回 ResponseEntity&lt;Resource&gt;
```java
@GetMapping("/download4")
public ResponseEntity<Resource> download4() throws IOException {
    /**
     * 通过 ResponseEntity 下载文件，body 为 org.springframework.core.io.Resource 类型
     * Resource是spring中的一个资源接口，是对资源的一种抽象，常见的几个实现类
     * ClassPathResource：classpath下面的文件资源
     * FileSystemResource：文件系统资源
     * InputStreamResource：流资源
     * ByteArrayResource：字节数组资源
     */
    Resource resource = new ClassPathResource("文件1.txt");
    //文件名编码，防止中文乱码
    String filename = URLEncoder.encode("文件1.txt", "UTF-8");
    //构建响应实体：ResponseEntity，ResponseEntity中包含了http请求的响应信息，比如状态码、头、body
    ResponseEntity<Resource> responseEntity = ResponseEntity.ok()
            .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + filename + "\"")
            .header(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_OCTET_STREAM_VALUE)
            .body(resource);
    return responseEntity;
}
```
![image-20240830174526993](/blogs/_archive-2024-assets/9444fd27308286fe8af9.webp)
看下效果，浏览器中访问：http://localhost:8080/download4
# 4、中文乱码
有些朋友可能遇到过，文件名中如果有中文，下载下来后文件名称是乱码
解决代码如下，需要对文件名称进行编码，具体大家可以看看上面的案例代码。
```java
//文件名编码，防止中文乱码
String filename = URLEncoder.encode(file.getName(), "UTF-8");
```
# 5、案例完整代码
源码在 lesson082 这个模块中，上面接口代码都在下面这个controller中
```java
com.itsoku.lesson082.FileController
```

# SpringBoot中实现一个通用Excel导出功能
## 这个导出功能的特色
- 非常通用，能够满足大部分项目中99%的导出功能，代码复用性很强
- 导出的列可以由前端自定义（比如哪些列需要导出、列的顺序、名称等都是可以由前端自定义）
## 看效果
先带大家看一下效果。
启动`com.itsoku.lesson007.Lesson008Application`，启动好之后，浏览器中打开`http://localhost:8080/userList`，看效果。
## 代码解析
```
com.itsoku.lesson007.controller.UserController#userExport
```
### 入参（ExcelExportRequest）
```java
public class ExcelExportRequest {
    /**
     * excel名称
     */
    private String excelName;
    /**
     * sheet的名称
     */
    private String sheetName;
    /**
     * 导出字段有序列表
     */
    private List<ExcelExportField> fieldList;
 }
```
### 出参（ExcelExportResponse）
```java
public class ExcelExportResponse {
    //导出的excel文件名称
    private String excelName;
    // sheet列表数据
    private List<ExcelSheet> sheetList;
}
```
### Aop拦截请求，将 ExcelExportResponse 处理成excel导出
```java
@Component
@Aspect
public class ExcelExportAspect {
    @Around(value = "execution(* com.itsoku..*Controller.*(..))")
    public Object around(ProceedingJoinPoint proceedingJoinPoint) throws Throwable {
        Object result = proceedingJoinPoint.proceed();
        if (result instanceof ExcelExportResponse) {
            //下载excel
            ExcelExportUtils.writeExcelToResponse((ExcelExportResponse) result);
            return null;
        } else {
            return result;
        }
    }
}
```
## 核心代码
![image-20240401201152691](/blogs/_archive-2024-assets/1f29b7e9ad9c5149ffd7.webp)

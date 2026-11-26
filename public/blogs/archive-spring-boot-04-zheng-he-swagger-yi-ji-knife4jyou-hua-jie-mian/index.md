因为是前后端项目，需要前端的参与，所以一个好看的接口文档非常的重要

## 1、引入依赖

美化插件其中自带swagger的依赖了

```jsx
<dependency>
    <groupId>com.github.xiaoymin</groupId>
    <artifactId>knife4j-spring-boot-starter</artifactId>
    <version>2.0.9</version>
</dependency>
```

## 2、添加配置类

```jsx
package com.abin.mallchat.common.common.config;

import org.springframework.boot.actuate.autoconfigure.endpoint.web.CorsEndpointProperties;
import org.springframework.boot.actuate.autoconfigure.endpoint.web.WebEndpointProperties;
import org.springframework.boot.actuate.autoconfigure.web.server.ManagementPortType;
import org.springframework.boot.actuate.endpoint.ExposableEndpoint;
import org.springframework.boot.actuate.endpoint.web.*;
import org.springframework.boot.actuate.endpoint.web.annotation.ControllerEndpointsSupplier;
import org.springframework.boot.actuate.endpoint.web.annotation.ServletEndpointsSupplier;
import org.springframework.boot.actuate.endpoint.web.servlet.WebMvcEndpointHandlerMapping;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.core.env.Environment;
import org.springframework.core.env.Profiles;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.config.annotation.EnableWebMvc;
import org.springframework.web.servlet.config.annotation.ViewControllerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import springfox.documentation.builders.ApiInfoBuilder;
import springfox.documentation.builders.PathSelectors;
import springfox.documentation.builders.RequestHandlerSelectors;
import springfox.documentation.service.Contact;
import springfox.documentation.spi.DocumentationType;
import springfox.documentation.spring.web.plugins.Docket;
import springfox.documentation.swagger2.annotations.EnableSwagger2WebMvc;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

/**
 * Description:
 * Author: <a href="<https://github.com/zongzibinbin>">abin</a>
 * Date: 2023-03-23
 */
@Configuration
@EnableSwagger2WebMvc
public class SwaggerConfig {
    @Bean(value = "defaultApi2")
    Docket docket() {
        return new Docket(DocumentationType.SWAGGER_2)
                //配置网站的基本信息
                .apiInfo(new ApiInfoBuilder()
                        //网站标题
                        .title("mallchat接口文档")
                        //标题后面的版本号
                        .version("v1.0")
                        .description("mallchat接口文档")
                        //联系人信息
                        .contact(new Contact("阿斌", "<http://www.mallchat.cn>", "972627721@qq.com"))
                        .build())
                .select()
                //指定接口的位置
                .apis(RequestHandlerSelectors
                        .withClassAnnotation(RestController.class)
                )
                .paths(PathSelectors.any())
                .build();
    }
    @Bean
    public WebMvcEndpointHandlerMapping webEndpointServletHandlerMapping(WebEndpointsSupplier webEndpointsSupplier, ServletEndpointsSupplier servletEndpointsSupplier, ControllerEndpointsSupplier controllerEndpointsSupplier, EndpointMediaTypes endpointMediaTypes, CorsEndpointProperties corsProperties, WebEndpointProperties webEndpointProperties, Environment environment) {
        List<ExposableEndpoint<?>> allEndpoints = new ArrayList();
        Collection<ExposableWebEndpoint> webEndpoints = webEndpointsSupplier.getEndpoints();
        allEndpoints.addAll(webEndpoints);
        allEndpoints.addAll(servletEndpointsSupplier.getEndpoints());
        allEndpoints.addAll(controllerEndpointsSupplier.getEndpoints());
        String basePath = webEndpointProperties.getBasePath();
        EndpointMapping endpointMapping = new EndpointMapping(basePath);
        boolean shouldRegisterLinksMapping = this.shouldRegisterLinksMapping(webEndpointProperties, environment, basePath);
        return new WebMvcEndpointHandlerMapping(endpointMapping, webEndpoints, endpointMediaTypes, corsProperties.toCorsConfiguration(), new EndpointLinksResolver(allEndpoints, basePath), shouldRegisterLinksMapping, null);
    }
    private boolean shouldRegisterLinksMapping(WebEndpointProperties webEndpointProperties, Environment environment, String basePath) {
        return webEndpointProperties.getDiscovery().isEnabled() && (StringUtils.hasText(basePath) || ManagementPortType.get(environment).equals(ManagementPortType.DIFFERENT));
    }
}
```

## 3、展示效果

优化前页面

![image-20240924201219202](/blogs/_archive-2024-assets/e2a9b4f102af7550a63e.webp)

优化后页面:http://localhost:8080/doc.html

差别还是很大的。

![image-20240924201227135](/blogs/_archive-2024-assets/81fb3fd3a17e3a722356.webp)

## 4、swagger使用

```java
//实体类
//entity的实体类中可以添加一些自定义设置
@Data
@EqualsAndHashCode(callSuper = false)
@ApiModel(value="IntegralGrade对象", description="积分等级表")
public class IntegralGrade implements Serializable {

    private static final long serialVersionUID = 1L;

    @ApiModelProperty(value = "编号")
      @TableId(value = "id", type = IdType.AUTO)
    private Long id;

    @ApiModelProperty(value = "积分区间开始")
    private Integer integralStart;

    @ApiModelProperty(value = "积分区间结束")
    private Integer integralEnd;

    @ApiModelProperty(value = "借款额度")
    private BigDecimal borrowAmount;

    @ApiModelProperty(value = "创建时间")
    private LocalDateTime createTime;

    @ApiModelProperty(value = "更新时间")
    private LocalDateTime updateTime;

    @ApiModelProperty(value = "逻辑删除(1:已删除，0:未删除)")
    @TableField("is_deleted")
    @TableLogic
    private Boolean deleted;
}
//controler层
@RestController
@RequestMapping("/admin/integralGrade")
@Api(value = "积分等级管理")
public class IntegralGradeController {

    @Resource
    private IntegralGradeService integralGradeService;

    @GetMapping("/list")
    @ApiOperation("积分等级列表")
    public Result listAll(){
        List<IntegralGrade> list = integralGradeService.list();
        return Result.ok().data("list",list);
    }

    @DeleteMapping("/remove/{id}")
    @ApiOperation(value = "根据id删除积分等级",notes = "逻辑删除")
    public Result removeById(
        @ApiParam(value = "数据id",required = true,example = "1")
        @PathVariable Long id){
        boolean result = integralGradeService.removeById(id);
        if (result){
            return Result.ok().message("删除成功");
        }else {
            return Result.error().message("删除失败");
        }
    }

    @PostMapping("/save")
    @ApiOperation(value = "新增积分等级")
    public Result save(@ApiParam(value = "积分等级对象",required = true) @RequestBody IntegralGrade integralGrade){
        boolean result = integralGradeService.save(integralGrade);
        if (result){
            return Result.ok().message("新增成功");
        }else {
            return Result.error().message("新增失败");
        }
    }

    @PutMapping("/updateById")
    @ApiOperation(value = "根据id修改积分等级")
    public Result updateById(@ApiParam(value = "积分等级对象",required = true) @RequestBody IntegralGrade integralGrade){
        boolean result = integralGradeService.updateById(integralGrade);
        if (result){
            return Result.ok().message("修改成功");
        }else {
            return Result.error().message("修改失败");
        }
    }

    @GetMapping("/getById/{id}")
    @ApiOperation(value = "根据id查询积分等级")
    public Result getById(@ApiParam(value = "数据id",required = true,example = "1") @PathVariable Long id){
        IntegralGrade result = integralGradeService.getById(id);
        if (result == null){
            return Result.error().message("查询失败");
        }else {
            return Result.ok().data("integralGrade",result);
        }
    }
}
```

## 5、bug解决

如果运行报错。`Failed to start bean ‘documentationPluginsBootstrapper`

是因为springboot2.6.x后会有兼容问题，Springboot2.6以后将SpringMVC 默认路径匹配策略从AntPathMatcher 更改为PathPatternParser，导致出错。

所以要么降springboot的版本，要么yml文件加上一个配置。

```jsx
spring:
  mvc:
    pathmatch:
      matching-strategy: ANT_PATH_MATCHER
```

配置类`SwaggerConfig`加上，上面的配置类已经包含，无需引入

```plain
@Bean
    public WebMvcEndpointHandlerMapping webEndpointServletHandlerMapping(WebEndpointsSupplier webEndpointsSupplier, ServletEndpointsSupplier servletEndpointsSupplier, ControllerEndpointsSupplier controllerEndpointsSupplier, EndpointMediaTypes endpointMediaTypes, CorsEndpointProperties corsProperties, WebEndpointProperties webEndpointProperties, Environment environment) {
        List<ExposableEndpoint<?>> allEndpoints = new ArrayList();
        Collection<ExposableWebEndpoint> webEndpoints = webEndpointsSupplier.getEndpoints();
        allEndpoints.addAll(webEndpoints);
        allEndpoints.addAll(servletEndpointsSupplier.getEndpoints());
        allEndpoints.addAll(controllerEndpointsSupplier.getEndpoints());
        String basePath = webEndpointProperties.getBasePath();
        EndpointMapping endpointMapping = new EndpointMapping(basePath);
        boolean shouldRegisterLinksMapping = this.shouldRegisterLinksMapping(webEndpointProperties, environment, basePath);
        return new WebMvcEndpointHandlerMapping(endpointMapping, webEndpoints, endpointMediaTypes, corsProperties.toCorsConfiguration(), new EndpointLinksResolver(allEndpoints, basePath), shouldRegisterLinksMapping, null);
    }
    private boolean shouldRegisterLinksMapping(WebEndpointProperties webEndpointProperties, Environment environment, String basePath) {
        return webEndpointProperties.getDiscovery().isEnabled() && (StringUtils.hasText(basePath) || ManagementPortType.get(environment).equals(ManagementPortType.DIFFERENT));
    }
```

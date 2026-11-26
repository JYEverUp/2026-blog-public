# 复杂业务，传参的痛点
## 从一段代码开始
```java
package com.itsoku.lesson016;
public class XxxService {
    /**
     * 这个方法是对外暴露的接口
     *
     * @param request
     */
    public void execute(M1Request request) {
        //m1方法中会产生Obj1,Obj2
        this.m1(request);
        //下面m2方法中要用到m1方法中产生的Obj1、Obj2，而m2本身又会返回obje3
        Obj1 obj1 = null;
        Obj2 obj2 = null;
        Obj3 obj3 = this.m2(obj1, obj2);
        //m3方法中又会用到4个参数：request、obj1、obj2、obj3
        this.m3(request, obj1, obj2, obj3);
    }
    private void m1(M1Request request) {
        System.out.println(request);
        //这里会产生2个对象
        Obj1 obj1 = new Obj1();
        Obj2 obj2 = new Obj2();
    }
    private Obj3 m2(Obj1 obj1, Obj2 obj2) {
        System.out.println(obj1);
        System.out.println(obj2);
        //这里需要用到 obj1,obj2
        Obj3 obj3 = new Obj3();
        return obj3;
    }
    private void m3(M1Request request, Obj1 obj1, Obj2 obj2, Obj3 obj3) {
        System.out.println(request);
        System.out.println(obj1);
        System.out.println(obj2);
        System.out.println(obj3);
    }
}
```
上面代码如何拿到m1方法中创建的2个对象呢？
如下，我们可以创建一个类，用来作为m1方法的返回值，用来存放m1方法中的ojb1、obj2
```java
public class M1Result {
    private Obj1 obj1;
    private Obj2 obj2;
    public Obj1 getObj1() {
        return obj1;
    }
    public void setObj1(Obj1 obj1) {
        this.obj1 = obj1;
    }
    public Obj2 getObj2() {
        return obj2;
    }
    public void setObj2(Obj2 obj2) {
        this.obj2 = obj2;
    }
}
```
## 优化后的代码
```java
package com.itsoku.lesson016;
public class XxxService1 {
    /**
     * 这个方法是对外暴露的接口
     *
     * @param request
     */
    public void execute(M1Request request) {
        //m1方法中会产生Obj1,Obj2
        M1Result m1Result = this.m1(request);
        //下面m2方法中要用到m1方法中产生的Obj1、Obj2
        Obj1 obj1 = m1Result.getObj1();
        Obj2 obj2 = m1Result.getObj2();
        Obj3 obj3 = this.m2(obj1, obj2);
        //m3方法中又会用到4个参数：request、obj1、obj2、obj3
        this.m3(request, obj1, obj2, obj3);
    }
    private M1Result m1(M1Request request) {
        System.out.println(request);
        Obj1 obj1 = new Obj1();
        Obj2 obj2 = new Obj2();
        M1Result result = new M1Result();
        result.setObj1(obj1);
        result.setObj2(obj2);
        return result;
    }
    private Obj3 m2(Obj1 obj1, Obj2 obj2) {
        System.out.println(obj1);
        System.out.println(obj2);
        //这里需要用到 obj1,obj2
        Obj3 obj3 = new Obj3();
        return obj3;
    }
    private void m3(M1Request request, Obj1 obj1, Obj2 obj2, Obj3 obj3) {
        System.out.println(request);
        System.out.println(obj1);
        System.out.println(obj2);
        System.out.println(obj3);
    }
}
```
假如execute方法中还有后续代码，如下
```java
public void execute(M1Request request) {
    //m1方法中会产生Obj1,Obj2
    M1Result m1Result = this.m1(request);
    //下面m2方法中要用到m1方法中产生的Obj1、Obj2
    Obj1 obj1 = m1Result.getObj1();
    Obj2 obj2 = m1Result.getObj2();
    Obj3 obj3 = this.m2(obj1, obj2);
    //m3方法中又会用到4个参数：request、obj1、obj2、obj3
    this.m3(request, obj1, obj2, obj3);
    // 下面还有其他业务方法，内部也会产生一些对象，后续一些方法可能需要用到这些对象，有没有更好的解决方案呢？
}
```
## 使用上下文对象来解决
可以创建一个上下文对象，为这个业务服务，上下文对象中存放了这个业务中所有需要用到的对象，这些对象都可以放到里面，后面的方法如果需要用到相关对象的时候，直接从上下文对象中存取就可以了。
本案例中我们可以定义一个上下文对象，通常以Context作为后缀，定义如下，目前这个案例中需要用到4个对象，都在这个类中包含了
```java
package com.itsoku.lesson016;
public class XxxContext {
    private  M1Request request;
    private Obj1 obj1;
    private Obj2 obj2;
    private Obj3 obj3;
    // getter、setter方法
}
```
引入这个上下文对象后，优化后的代码，如下，重点在于方法的参数类型都改成了 XxxContext，这样在方法中就可以从这个上线文中获取到需要使用的对象了，产生的新对象也可以丢到里面，是不是方便了很多？
```java
package com.itsoku.lesson016;
public class XxxService3 {
    /**
     * 这个方法是对外暴露的接口
     *
     * @param request
     */
    public void execute(M1Request request) {
        XxxContext context = new XxxContext();
        //m1方法中会产生Obj1,Obj2
        this.m1(context);
        //下面m2方法中要用到m1方法中产生的Obj1、Obj2
        this.m2(context);
        //m3方法中又会用到4个参数：request、obj1、obj2、obj3
        this.m3(context);
        // 下面还有其他业务方法，内部也会产生一些对象，后续一些方法可能需要用到这些对象，有没有更好的解决方案呢？
        this.otherMethod(context);
    }
    private void m1(XxxContext context) {
        System.out.println(context.getRequest());
        Obj1 obj1 = new Obj1();
        Obj2 obj2 = new Obj2();
        context.setObj1(obj1);
        context.setObj2(obj2);
    }
    private void m2(XxxContext context) {
        //这里需要用到 obj1,obj2
        System.out.println(context.getObj1());
        System.out.println(context.getObj2());
        Obj3 obj3 = new Obj3();
        context.setObj3(obj3);
    }
    private void m3(XxxContext context) {
        System.out.println(context.getRequest());
        System.out.println(context.getObj1());
        System.out.println(context.getObj2());
        System.out.println(context.getObj3());
    }
    private void otherMethod(XxxContext context) {
    }
}
```

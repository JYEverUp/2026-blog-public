## 一、Java常用类

### String类

java.lang.String类的使用

1. 概述

   String:字符串，使用一对""引起来表示。

   1. String声明为final的，不可被继承

   2. String实现了Serializable接口：表示字符串是支持序列化的。

      实现了Comparable接口：表示String可以比较大小

   3. String内部定义了final char[] value用于存储字符串数据

   4. 通过字面量的方式（区别于new给一个字符串赋值，此时的字符串值声明在字符串常量池中)。

   5. 字符串常量池中是不会存储相同内容(使用String类的equals()比较，返回true)的字符串的。

2. String的不可变性

   1. 说明

      1. 当对字符串重新赋值时，需要重写指定内存区域赋值，不能使用原有的value进行赋值。
      2. 当对现的字符串进行连接操作时，也需要重新指定内存区域赋值，不能使用原有的value进行赋值。
      3. 当调用String的replace()方法修改指定字符或字符串时，也需要重新指定内存区域赋值，不能使用原有的value进行赋值。

   2. 代码举例

      ```java
      String s1 = "abc";//字面量的定义方式
      String s2 = "abc";
      s1 = "hello";
      
      System.out.println(s1 == s2);//比较s1和s2的地址值
      
      System.out.println(s1);//hello
      System.out.println(s2);//abc
      
      System.out.println("*****************");
      
      String s3 = "abc";
      s3 += "def";
      System.out.println(s3);//abcdef
      System.out.println(s2);
      
      System.out.println("*****************");
      
      String s4 = "abc";
      String s5 = s4.replace('a', 'm');
      System.out.println(s4);//abc
      System.out.println(s5);//mbc
      ```

      

   3. 图示

      ![image-20211128150727913](/blogs/_archive-2024-assets/6ef521997c85d5b34c4c.webp)

3. String实例化的不同方式

   1. 方式说明

      1. 方式一：通过字面量定义的方式
      2. 方式二：通过new + 构造器的方式

   2. 代码举例

      ```java
      //通过字面量定义的方式：此时的s1和s2的数据javaEE声明在方法区中的字符串常量池中。
      String s1 = "javaEE";
      String s2 = "javaEE";
      //通过new + 构造器的方式:此时的s3和s4保存的地址值，是数据在堆空间中开辟空间以后对应的地址值。
      String s3 = new String("javaEE");
      String s4 = new String("javaEE");
      
      System.out.println(s1 == s2);//true
      System.out.println(s1 == s3);//false
      System.out.println(s1 == s4);//false
      System.out.println(s3 == s4);//false
      ```

      

   3. 面试题：String s = new String("abc");方式创建对象，在内存中创建了几个对象？

      答案：两个:一个是堆空间中new结构，另一个是char[]对应的常量池中的数据："abc"

   4. 图示

      ![image-20211128150842221](/blogs/_archive-2024-assets/7737cef3febd974dc6f7.webp)

4. 字符串拼接方式赋值的对比

   1. 说明

      1. 常量与常量的拼接结果在常量池。且常量池中不会存在相同内容的常量。
      2. 只要其中一个是变量，结果就在堆中。
      3. 如果拼接的结果调用intern()方法，返回值就在常量池中

   2. 代码举例

      ```java
      String s1 = "javaEE";
      String s2 = "hadoop";
      
      String s3 = "javaEEhadoop";
      String s4 = "javaEE" + "hadoop";
      String s5 = s1 + "hadoop";
      String s6 = "javaEE" + s2;
      String s7 = s1 + s2;
      
      System.out.println(s3 == s4);//true
      System.out.println(s3 == s5);//false
      System.out.println(s3 == s6);//false
      System.out.println(s3 == s7);//false
      System.out.println(s5 == s6);//false
      System.out.println(s5 == s7);//false
      System.out.println(s6 == s7);//false
      
      String s8 = s6.intern();//返回值得到的s8使用的常量值中已经存在的“javaEEhadoop”
      System.out.println(s3 == s8);//true
      ****************************
      String s1 = "javaEEhadoop";
      String s2 = "javaEE";
      String s3 = s2 + "hadoop";
      System.out.println(s1 == s3);//false
      
      final String s4 = "javaEE";//s4:常量
      String s5 = s4 + "hadoop";
      System.out.println(s1 == s5);//true
      
      ```

      

5. 常用方法：

   ```java
   int length()：返回字符串的长度： return value.length
   char charAt(int index)： 返回某索引处的字符return value[index]
   boolean isEmpty()：判断是否是空字符串：return value.length == 0
   String toLowerCase()：使用默认语言环境，将 String 中的所字符转换为小写
   String toUpperCase()：使用默认语言环境，将 String 中的所字符转换为大写
   String trim()：返回字符串的副本，忽略前导空白和尾部空白
   boolean equals(Object obj)：比较字符串的内容是否相同
   boolean equalsIgnoreCase(String anotherString)：与equals方法类似，忽略大小写
   String concat(String str)：将指定字符串连接到此字符串的结尾。 等价于用“+”
   int compareTo(String anotherString)：比较两个字符串的大小
   String substring(int beginIndex)：
       返回一个新的字符串，它是此字符串的从beginIndex开始截取到最后的一个子字符串。
   String substring(int beginIndex, int endIndex) ：
       返回一个新字符串，它是此字符串从beginIndex开始截取到endIndex(不包含)的一个子字符串。
   
   boolean endsWith(String suffix)：测试此字符串是否以指定的后缀结束
   boolean startsWith(String prefix)：测试此字符串是否以指定的前缀开始
   boolean startsWith(String prefix, int toffset)：
       测试此字符串从指定索引开始的子字符串是否以指定前缀开始
   
   boolean contains(CharSequence s)：当且仅当此字符串包含指定的 char 值序列时，返回 true
   int indexOf(String str)：返回指定子字符串在此字符串中第一次出现处的索引
   int indexOf(String str, int fromIndex)：
       返回指定子字符串在此字符串中第一次出现处的索引，从指定的索引开始
   int lastIndexOf(String str)：返回指定子字符串在此字符串中最右边出现处的索引
   int lastIndexOf(String str, int fromIndex)：
       返回指定子字符串在此字符串中最后一次出现处的索引，从指定的索引开始反向搜索
   
   注：indexOf和lastIndexOf方法如果未找到都是返回-1
   
   替换：
   String replace(char oldChar, char newChar)：
       返回一个新的字符串，它是通过用 newChar 替换此字符串中出现的所 oldChar 得到的。
   String replace(CharSequence target, CharSequence replacement)：
       使用指定的字面值替换序列替换此字符串所匹配字面值目标序列的子字符串。
   String replaceAll(String regex, String replacement)：
       使用给定的 replacement 替换此字符串所匹配给定的正则表达式的子字符串。
   String replaceFirst(String regex, String replacement)：
       使用给定的 replacement 替换此字符串匹配给定的正则表达式的第一个子字符串。
   匹配:
   boolean matches(String regex)：告知此字符串是否匹配给定的正则表达式。
   切片：
   String[] split(String regex)：根据给定正则表达式的匹配拆分此字符串。
   String[] split(String regex, int limit)：根据匹配给定的正则表达式来拆分此字符串，
       最多不超过limit个，如果超过了，剩下的全部都放到最后一个元素中。
   
   ```

   

6. String与其它结构的转换

   1. 与基本数据类型、包装类之间的转换

      1. String --> 基本数据类型、包装类：调用包装类的静态方法：parseXxx(str)
             

      2. 基本数据类型、包装类 --> String:调用String重载的valueOf(xxx)

         ```java
            @Test
             public void test1(){
                 String str1 = "123";
         //        int num = (int)str1;//错误的
                 int num = Integer.parseInt(str1);
         
                 String str2 = String.valueOf(num);//"123"
                 String str3 = num + "";
         
                 System.out.println(str1 == str3);
             }
         
         ```

   2. 与字符数组之间的转换

      1. String --> char[]:调用String的toCharArray()

      2. char[] --> String:调用String的构造器

         ```java
         @Test
         public void test2(){
             String str1 = "abc123";  //题目： a21cb3
         
             char[] charArray = str1.toCharArray();
             for (int i = 0; i < charArray.length; i++) {
                 System.out.println(charArray[i]);
             }
         
             char[] arr = new char[]{'h','e','l','l','o'};
             String str2 = new String(arr);
             System.out.println(str2);
         }
         
         ```

         

   3. 与字节数组之间的转换

      1. 编码：String --> byte[]:调用String的getBytes()
      2. 解码：byte[] --> String:调用String的构造器

      - 编码：字符串 -->字节  (看得懂 --->看不懂的二进制数据)

      - 解码：编码的逆过程，字节 --> 字符串 （看不懂的二进制数据 ---> 看得懂

      - 说明：解码时，要求解码使用的字符集必须与编码时使用的字符集一致，否则会出现乱码。

        ```java
        @Test
        public void test3() throws UnsupportedEncodingException {
            String str1 = "abc123中国";
            byte[] bytes = str1.getBytes();//使用默认的字符集，进行编码。
            System.out.println(Arrays.toString(bytes));
        
            byte[] gbks = str1.getBytes("gbk");//使用gbk字符集进行编码。
            System.out.println(Arrays.toString(gbks));
        
            System.out.println("******************");
        
            String str2 = new String(bytes);//使用默认的字符集，进行解码。
            System.out.println(str2);
        
            String str3 = new String(gbks);
            System.out.println(str3);//出现乱码。原因：编码集和解码集不一致！
        
        
            String str4 = new String(gbks, "gbk");
            System.out.println(str4);//没出现乱码。原因：编码集和解码集一致！
        }
        ```

        

   4. 与StringBuffer、StringBuilder之间的转换

      1. String -->StringBuffer、StringBuilder:调用StringBuffer、StringBuilder构造器
      2. StringBuffer、StringBuilder -->String:①调用String构造器；②StringBuffer、StringBuilder的toString()

7. JVM中字符串常量池存放位置说明：

   1. jdk 1.6 (jdk 6.0 ,java 6.0):字符串常量池存储在方法区（永久区）
   2. jdk 1.7:字符串常量池存储在堆空间
   3. jdk 1.8:字符串常量池存储在方法区（元空间）

8. 常见算法题目的考查：

   1. 模拟一个trim方法，去除字符串两端的空格。

   2. 将一个字符串进行反转。将字符串中指定部分进行反转。比如“abcdefg”反转为”abfedcg”

   3. 获取一个字符串在另一个字符串中出现的次数。
          比如：获取“ ab”在 “abkkcadkabkebfkabkskab” 中出现的次数

   4. 获取两个字符串中最大相同子串。比如：
      str1 = "abcwerthelloyuiodef“;str2 = "cvhellobnm"

      提示：将短的那个串进行长度依次递减的子串与较长的串比较。

   5. 对字符串中字符进行自然顺序排序。

      提示：

      1. 字符串变成字符数组。
      2. 对数组排序，择，冒泡，Arrays.sort();
      3. 将排序后的数组变成字符串。

### StringBuffer、StringBuilder

1. String、StringBuffer、StringBuilder三者的对比

   1. String:不可变的字符序列；底层使用char[]存储
   2. StringBuffer:可变的字符序列；线程安全的，效率低；底层使用char[]存储
   3. StringBuilder:可变的字符序列；jdk5.0新增的，线程不安全的，效率高；底层使用char[]存储

2. StringBuffer与StringBuilder的内存解析

   以StringBuffer为例：

   ```java
   String str = new String();//char[] value = new char[0];
   String str1 = new String("abc");//char[] value = new char[]{'a','b','c'};
   
   StringBuffer sb1 = new StringBuffer();
   //char[] value = new char[16];底层创建了一个长度是16的数组。
   
   System.out.println(sb1.length());//
   sb1.append('a');//value[0] = 'a';
   sb1.append('b');//value[1] = 'b';
   
   StringBuffer sb2 = new StringBuffer("abc");
   //char[] value = new char["abc".length() + 16];
   
   //问题1. System.out.println(sb2.length());//3
   //问题2. 扩容问题:如果要添加的数据底层数组盛不下了，那就需要扩容底层的数组。
            默认情况下，扩容为原来容量的2倍 + 2，同时将原数组中的元素复制到新的数组中。
   
   指导意义：开发中建议大家使用：StringBuffer(int capacity) 或 StringBuilder(int capacity)
   ```

3. 对比String、StringBuffer、StringBuilder三者的执行效率

   从高到低排列：StringBuilder > StringBuffer > String

4. StringBuffer、StringBuilder中的常用方法

   - 增：append(xxx)
   - 删：delete(int start,int end)
   - 改：setCharAt(int n ,char ch) / replace(int start, int end, String str)
   - 查：charAt(int n )
   - 插：insert(int offset, xxx)
   - 长度：length();
   - 遍历：for() + charAt() / toString()

### JDK 8之前日期时间API

1. 获取系统当前时间：System类中的currentTimeMillis()

   ```java
   long time = System.currentTimeMillis();
   //返回当前时间与1970年1月1日0时0分0秒之间以毫秒为单位的时间差。
   //称为时间戳
   System.out.println(time);
   ```

   

2. java.util.Date类与java.sql.Date类

   java.util.Date类
              

   ​		|---java.sql.Date类

   1. 两个构造器的使用

      1. 构造器一：Date()：创建一个对应当前时间的Date对象
      2. 构造器二：创建指定毫秒数的Date对象

   2. 两个方法的使用

      1. toString():显示当前的年、月、日、时、分、秒
      2. getTime():获取当前Date对象对应的毫秒数。（时间戳）

   3. java.sql.Date对应着数据库中的日期类型的变量

      1. 如何实例化
      2. 如何将java.util.Date对象转换为java.sql.Date对象

      ```java
          @Test
          public void test2(){
              //构造器一：Date()：创建一个对应当前时间的Date对象
              Date date1 = new Date();
              System.out.println(date1.toString());//Sat Feb 16 16:35:31 GMT+08:00 2019
      
              System.out.println(date1.getTime());//1550306204104
      
              //构造器二：创建指定毫秒数的Date对象
              Date date2 = new Date(155030620410L);
              System.out.println(date2.toString());
      
              //创建java.sql.Date对象
              java.sql.Date date3 = new java.sql.Date(35235325345L);
              System.out.println(date3);//1971-02-13
      
              //如何将java.util.Date对象转换为java.sql.Date对象
              //情况一：
      //        Date date4 = new java.sql.Date(2343243242323L);
      //        java.sql.Date date5 = (java.sql.Date) date4;
              //情况二：
              Date date6 = new Date();
              java.sql.Date date7 = new java.sql.Date(date6.getTime());
      
      
          }
      ```

      

3. java.text.SimpleDataFormat类

   SimpleDateFormat对日期Date类的格式化和解析

   1. 两个操作：

      1. 格式化：日期 --->字符串
      2. 解析：格式化的逆过程，字符串 ---> 日期

   2. SimpleDateFormat的实例化:new + 构造器

      ```java
      /*************照指定的方式格式化和解析：调用带参的构造器*****************
      //        SimpleDateFormat sdf1 = new SimpleDateFormat("yyyyy.MMMMM.dd GGG hh:mm aaa");
              SimpleDateFormat sdf1 = new SimpleDateFormat("yyyy-MM-dd hh:mm:ss");
              //格式化
              String format1 = sdf1.format(date);
              System.out.println(format1);//2019-02-18 11:48:27
              //解析:要求字符串必须是符合SimpleDateFormat识别的格式(通过构造器参数体现),
              //否则，抛异常
              Date date2 = sdf1.parse("2020-02-18 11:48:27");
              System.out.println(date2);
      
      ```

      

   3. 小练习：

      ```java
      /*
          练习一：字符串"2020-09-08"转换为java.sql.Date
      
          练习二："天打渔两天晒网"   1990-01-01  xxxx-xx-xx 打渔？晒网？
      
          举例：2020-09-08 ？ 总天数
      
          总天数 % 5 == 1,2,3 : 打渔
          总天数 % 5 == 4,0 : 晒网
      
          总天数的计算？
          方式一：( date2.getTime() - date1.getTime()) / (1000 * 60 * 60 * 24) + 1
          方式二：1990-01-01  --> 2019-12-31  +  2020-01-01 -->2020-09-08
           */
          @Test
          public void testExer() throws ParseException {
              String birth = "2020-09-08";
      
              SimpleDateFormat sdf1 = new SimpleDateFormat("yyyy-MM-dd");
              Date date = sdf1.parse(birth);
      //        System.out.println(date);
      
              java.sql.Date birthDate = new java.sql.Date(date.getTime());
              System.out.println(birthDate);
          }
      ```

4. Calendar类：日历类、抽象类

   ```java
   		//1.实例化
           //方式一：创建其子类（GregorianCalendar的对象
           //方式二：调用其静态方法getInstance()
           Calendar calendar = Calendar.getInstance();
   //        System.out.println(calendar.getClass());
   
           //2.常用方法
           //get()
           int days = calendar.get(Calendar.DAY_OF_MONTH);
           System.out.println(days);
           System.out.println(calendar.get(Calendar.DAY_OF_YEAR));
   
           //set()
           //calendar可变性
            calendar.set(Calendar.DAY_OF_MONTH,22);
           days = calendar.get(Calendar.DAY_OF_MONTH);
           System.out.println(days);
   
           //add()
           calendar.add(Calendar.DAY_OF_MONTH,-3);
           days = calendar.get(Calendar.DAY_OF_MONTH);
           System.out.println(days);
   
           //getTime():日历类---> Date
           Date date = calendar.getTime();
           System.out.println(date);
   
           //setTime():Date ---> 日历类
           Date date1 = new Date();
           calendar.setTime(date1);
           days = calendar.get(Calendar.DAY_OF_MONTH);
           System.out.println(days);
   
   
   ```

### JDK8中新日期时间API

1. 日期时间API的迭代：

   1. 第一代：jdk 1.0 Date类
   2. 第二代：jdk 1.1 Calendar类，一定程度上替换Date类
   3. 第三代：jdk 1.8 提出了新的一套API

2. 前两代存在的问题举例：

   1. 可变性：像日期和时间这样的类应该是不可变的。
   2. 偏移性：Date中的年份是从1900开始的，而月份都从0开始。
   3. 格式化：格式化只对Date用，Calendar则不行。
   4. 此外，它们也不是线程安全的；不能处理闰秒等。

3. java 8 中新的日期时间API涉及到的包

   ![image-20211129090710926](/blogs/_archive-2024-assets/6b80c9ada9d8c0ee1da5.webp)

   

4. 本地日期、本地时间、本地日期时间的使用：LocalDate / LocalTime / LocalDateTime

   1. 说明：

      1. 分别表示使用 ISO-8601日历系统的日期、时间、日期和时间。它们提供了简单的本地日期或时间，并不包含当前的时间信息，也不包含与时区相关的信息。
      2. LocalDateTime相较于LocalDate、LocalTime，使用频率要高
      3. 类似于Calendar

   2. 常用方法：

      ![image-20211129090811575](/blogs/_archive-2024-assets/e75230bf9b234c442608.webp)

5. 时间点：Instant

   1. 说明：

      1. 时间线上的一个瞬时点。 概念上讲，它只是简单的表示自1970年1月1日0时0分0秒（UTC开始的秒数。）
      2. 类似于 java.util.Date类

   2. 常用方法：

      ![image-20211129090842611](/blogs/_archive-2024-assets/853227df559edae76928.webp)

6. 日期时间格式化类：DateTimeFormatter

   1. 说明：

      1. 格式化或解析日期、时间
      2. 类似于SimpleDateFormat

   2. 常用方法：

      ![image-20211129091037317](/blogs/_archive-2024-assets/5728854743ae3c908d59.webp)

      - 预定义的标准格式。如：ISO_LOCAL_DATE_TIME;ISO_LOCAL_DATE;ISO_LOCAL_TIME

      - 本地化相关的格式。如：ofLocalizedDateTime(FormatStyle.LONG)

      - 自定义的格式。如：ofPattern(“yyyy-MM-dd hh:mm:ss”)

        ```java
        //  重点：自定义的格式。如：ofPattern(“yyyy-MM-dd hh:mm:ss”)
        DateTimeFormatter formatter3 = DateTimeFormatter.ofPattern("yyyy-MM-dd hh:mm:ss");
        //格式化
        String str4 = formatter3.format(LocalDateTime.now());
        System.out.println(str4);//2019-02-18 03:52:09
        
        //解析
        TemporalAccessor accessor = formatter3.parse("2019-02-18 03:52:09");
        System.out.println(accessor);
        ```

7. 其它API的使用 （不讲）

   1. 带时区的日期时间：ZonedDateTime / ZoneId 
      举例：

      ```java
      // ZoneId:类中包含了所的时区信息
      	@Test
      	public void test1(){
      		//getAvailableZoneIds():获取所的ZoneId
      		Set<String> zoneIds = ZoneId.getAvailableZoneIds();
      		for(String s : zoneIds){
      			System.out.println(s);
      		}
      		System.out.println();
      		
      		//获取“Asia/Tokyo”时区对应的时间
      		LocalDateTime localDateTime = LocalDateTime.now(ZoneId.of("Asia/Tokyo"));
      		System.out.println(localDateTime);
      		
      		
      	}
      //ZonedDateTime:带时区的日期时间
      	@Test
      	public void test2(){
      		//now():获取本时区的ZonedDateTime对象
      		ZonedDateTime zonedDateTime = ZonedDateTime.now();
      		System.out.println(zonedDateTime);
      		//now(ZoneId id):获取指定时区的ZonedDateTime对象
      		ZonedDateTime zonedDateTime1 = ZonedDateTime.now(ZoneId.of("Asia/Tokyo"));
      		System.out.println(zonedDateTime1);
      	}
      ```

      

   2. 时间间隔：Duration--用于计算两个“时间”间隔，以秒和纳秒为基准

      ![image-20211129091228463](/blogs/_archive-2024-assets/3793a49933ae1cf62c14.webp)

      举例：

      ```java
      	@Test
      	public void test3(){
      		LocalTime localTime = LocalTime.now();
      		LocalTime localTime1 = LocalTime.of(15, 23, 32);
      		//between():静态方法，返回Duration对象，表示两个时间的间隔
      		Duration duration = Duration.between(localTime1, localTime);
      		System.out.println(duration);
      		
      		System.out.println(duration.getSeconds());
      		System.out.println(duration.getNano());
      		
      		LocalDateTime localDateTime = LocalDateTime.of(2016, 6, 12, 15, 23, 32);
      		LocalDateTime localDateTime1 = LocalDateTime.of(2017, 6, 12, 15, 23, 32);
      		
      		Duration duration1 = Duration.between(localDateTime1, localDateTime);
      		System.out.println(duration1.toDays());
      		
      	}
      ```

      

   3. 日期间隔：Period --用于计算两个“日期”间隔，以年、月、日衡量

      ![image-20211129091310779](/blogs/_archive-2024-assets/2e81b20987688cacabdb.webp)

      举例：

      ```java
      	@Test
      	public void test4(){
      		LocalDate localDate = LocalDate.now();
      		LocalDate localDate1 = LocalDate.of(2028, 3, 18);
      		
      		Period period = Period.between(localDate, localDate1);
      		System.out.println(period);
      		
      		System.out.println(period.getYears());
      		System.out.println(period.getMonths());
      		System.out.println(period.getDays());
      		
      		Period period1 = period.withYears(2);
      		System.out.println(period1);
      		
      	}
      ```

      

   4. 日期时间校正器：TemporalAdjuster举例：

      ```java
      	@Test
      	public void test5(){
      		//获取当前日期的下一个周日是哪天？
      		TemporalAdjuster temporalAdjuster = TemporalAdjusters.next(DayOfWeek.SUNDAY);
      		
      		LocalDateTime localDateTime = LocalDateTime.now().with(temporalAdjuster);
      		System.out.println(localDateTime);
      		
      		//获取下一个工作日是哪天？
      		LocalDate localDate = LocalDate.now().with(new TemporalAdjuster(){
      
      			@Override
      			public Temporal adjustInto(Temporal temporal) {
      				LocalDate date = (LocalDate)temporal;
      				if(date.getDayOfWeek().equals(DayOfWeek.FRIDAY)){
      					return date.plusDays(3);
      				}else if(date.getDayOfWeek().equals(DayOfWeek.SATURDAY)){
      					return date.plusDays(2);
      				}else{
      					return date.plusDays(1);
      				}
      					
      			}
      			
      		});
      		
      		System.out.println("下一个工作日是：" + localDate);
      	}
      ```

      

### Java比较器

1. Java比较器的使用背景：

   1. Java中的对象，正常情况下，只能进行比较：==  或  != 。不能使用 > 或 < 的
      但是在开发场景中，我们需要对多个对象进行排序，言外之意，就需要比较对象的大小。
   2. 如何实现？使用两个接口中的任何一个：Comparable 或 Comparator

2. 自然排序：使用Comparable接口

   1. 说明

      1. 像String、包装类等实现了Comparable接口，重写了compareTo(obj)方法，给出了比较两个对象大小的方式。
      2. 像String、包装类重写compareTo()方法以后，进行了从小到大的排列
      3. 重写compareTo(obj)的规则：
         1. 如果当前对象this大于形参对象obj，则返回正整数，
         2. 如果当前对象this小于形参对象obj，则返回负整数，
         3. 如果当前对象this等于形参对象obj，则返回零。
      4. 对于自定义类来说，如果需要排序，我们可以让自定义类实现Comparable接口，重写compareTo(obj)方法。在compareTo(obj)方法中指明如何排序

   2. 自定义类代码举例：

      ```java
      public class Goods implements  Comparable{
      
          private String name;
          private double price;
      
          //指明商品比较大小的方式:照价格从低到高排序,再照产品名称从高到低排序
          @Override
          public int compareTo(Object o) {
      //        System.out.println("**************");
              if(o instanceof Goods){
                  Goods goods = (Goods)o;
                  //方式一：
                  if(this.price > goods.price){
                      return 1;
                  }else if(this.price < goods.price){
                      return -1;
                  }else{
      //                return 0;
                     return -this.name.compareTo(goods.name);
                  }
                  //方式二：
      //           return Double.compare(this.price,goods.price);
              }
      //        return 0;
              throw new RuntimeException("传入的数据类型不一致！");
          }
      // getter、setter、toString()、构造器：省略
      }
      
      ```

      

3. 定制排序：使用Comparator接口

   1. 说明

      1. 背景：当元素的类型没实现java.lang.Comparable接口而又不方便修改代码，或者实现了java.lang.Comparable接口的排序规则不适合当前的操作，那么可以考虑使用 Comparator 的对象来排序
      2. 重写compare(Object o1,Object o2)方法，比较o1和o2的大小：
         - 如果方法返回正整数，则表示o1大于o2；
         - 如果返回0，表示相等；
         - 返回负整数，表示o1小于o2。

   2. 代码举例：

      ```java
      Comparator com = new Comparator() {
          //指明商品比较大小的方式:照产品名称从低到高排序,再照价格从高到低排序
          @Override
          public int compare(Object o1, Object o2) {
              if(o1 instanceof Goods && o2 instanceof Goods){
                  Goods g1 = (Goods)o1;
                  Goods g2 = (Goods)o2;
                  if(g1.getName().equals(g2.getName())){
                      return -Double.compare(g1.getPrice(),g2.getPrice());
                  }else{
                      return g1.getName().compareTo(g2.getName());
                  }
              }
              throw new RuntimeException("输入的数据类型不一致");
          }
      }
      
      使用：
      Arrays.sort(goods,com);
      Collections.sort(coll,com);
      new TreeSet(com);
      ```

      

4. 两种排序方式对比

   1. Comparable接口的方式一旦一定，保证Comparable接口实现类的对象在任何位置都可以比较大小。
   2. Comparator接口属于临时性的比较。

### 其他类

1. System类

   1. System类代表系统，系统级的很多属性和控制方法都放置在该类的内部。该类位于java.lang包。
   2. 由于该类的构造器是private的，所以无法创建该类的对象，也就是无法实例化该类。其内部的成员变量和成员方法都是static的，所以也可以很方便的进行调用。
   3. 方法：
      1. native long currentTimeMillis()
      2. void exit(int status)
      3. void gc()
      4. String getProperty(String key)

2. Math类：java.lang.Math提供了一系列静态方法用于科学计算。其方法的参数和返回值类型一般为double型。

3. BigInteger类、BigDecimal类

   1. 说明：

      1. java.math包的BigInteger可以表示不可变的任意精度的整数。
      2. 要求数字精度比较高，用到java.math.BigDecimal类

   2. 代码举例：

      ![image-20211129092157612](/blogs/_archive-2024-assets/b499d981a8b013afd9dc.webp)

## 二、枚举类和注解

### 枚举类的使用

1. 枚举类的说明：

   1. 枚举类的理解：类的对象只有有限个，确定的。我们称此类为枚举类
   2. 当需要定义一组常量时，强烈建议使用枚举类
   3. 如果枚举类中只一个对象，则可以作为单例模式的实现方式。

2. 如何自定义枚举类？步骤：

   ```java
   //自定义枚举类
   class Season{
       //1.声明Season对象的属性:private final修饰
       private final String seasonName;
       private final String seasonDesc;
   
       //2.私化类的构造器,并给对象属性赋值
       private Season(String seasonName,String seasonDesc){
           this.seasonName = seasonName;
           this.seasonDesc = seasonDesc;
       }
   
       //3.提供当前枚举类的多个对象：public static final的
       public static final Season SPRING = new Season("春天","春暖花开");
       public static final Season SUMMER = new Season("夏天","夏日炎炎");
       public static final Season AUTUMN = new Season("秋天","秋高气爽");
       public static final Season WINTER = new Season("冬天","冰天雪地");
   
       //4.其他诉求1：获取枚举类对象的属性
       public String getSeasonName() {
           return seasonName;
       }
   
       public String getSeasonDesc() {
           return seasonDesc;
       }
       //4.其他诉求1：提供toString()
       @Override
       public String toString() {
           return "Season{" +
                   "seasonName='" + seasonName + '\'' +
                   ", seasonDesc='" + seasonDesc + '\'' +
                   '}';
       }
   }
   
   ```

   

3. jdk 5.0 新增使用enum定义枚举类。步骤：

   ```java
   //使用enum关键字枚举类
   enum Season1 {
       //1.提供当前枚举类的对象，多个对象之间用","隔开，末尾对象";"结束
       SPRING("春天","春暖花开"),
       SUMMER("夏天","夏日炎炎"),
       AUTUMN("秋天","秋高气爽"),
       WINTER("冬天","冰天雪地");
   
       //2.声明Season对象的属性:private final修饰
       private final String seasonName;
       private final String seasonDesc;
   
       //2.私化类的构造器,并给对象属性赋值
   
       private Season1(String seasonName,String seasonDesc){
           this.seasonName = seasonName;
           this.seasonDesc = seasonDesc;
       }
   
       //4.其他诉求1：获取枚举类对象的属性
       public String getSeasonName() {
           return seasonName;
       }
   
       public String getSeasonDesc() {
           return seasonDesc;
       }
   
   }
   ```

   

4. 使用enum定义枚举类之后，枚举类常用方法：（继承于java.lang.Enum类）

   ```java
   Season1 summer = Season1.SUMMER;
           //toString():返回枚举类对象的名称
           System.out.println(summer.toString());
   
   //        System.out.println(Season1.class.getSuperclass());
           System.out.println("****************");
           //values():返回所的枚举类对象构成的数组
           Season1[] values = Season1.values();
           for(int i = 0;i < values.length;i++){
               System.out.println(values[i]);
           }
           System.out.println("****************");
           Thread.State[] values1 = Thread.State.values();
           for (int i = 0; i < values1.length; i++) {
               System.out.println(values1[i]);
           }
   
           //valueOf(String objName):返回枚举类中对象名是objName的对象。
           Season1 winter = Season1.valueOf("WINTER");
           //如果没objName的枚举类对象，则抛异常：IllegalArgumentException
   //        Season1 winter = Season1.valueOf("WINTER1");
           System.out.println(winter);
   ```

   

5. 使用enum定义枚举类之后，如何让枚举类对象分别实现接口：

   ```java
   interface Info{
       void show();
   }
   
   //使用enum关键字枚举类
   enum Season1 implements Info{
       //1.提供当前枚举类的对象，多个对象之间用","隔开，末尾对象";"结束
       SPRING("春天","春暖花开"){
           @Override
           public void show() {
               System.out.println("春天在哪里？");
           }
       },
       SUMMER("夏天","夏日炎炎"){
           @Override
           public void show() {
               System.out.println("宁夏");
           }
       },
       AUTUMN("秋天","秋高气爽"){
           @Override
           public void show() {
               System.out.println("秋天不回来");
           }
       },
       WINTER("冬天","冰天雪地"){
           @Override
           public void show() {
               System.out.println("大约在冬季");
           }
       };
   }
   
   ```



### 注解的使用

1. 注解的理解

   1. jdk 5.0 新增的功能

   2. Annotation 其实就是代码里的特殊标记, 这些标记可以在编译, 类加载, 运行时被读取, 并执行相应的处理。通过使用 Annotation,程序员可以在不改变原逻辑的情况下, 在源文件中嵌入一些补充信息。

   3. 在JavaSE中，注解的使用目的比较简单，例如标记过时的功能，忽略警告等。在JavaEE/Android中注解占据了更重要的角色，例如用来配置应用程序的任何切面，代替JavaEE旧版中所遗留的繁冗代码和XML配置等。

      **框架 = 注解 + 反射机制 + 设计模式**

2. 注解的使用示例

   1. 示例一：生成文档相关的注解
   2. 示例二：在编译时进行格式检查(JDK内置的个基本注解)
      1. @Override: 限定重写父类方法, 该注解只能用于方法

      2. @Deprecated: 用于表示所修饰的元素(类, 方法等)已过时。通常是因为所修饰的结构危险或存在更好的择

      3. @SuppressWarnings: 抑制编译器警告
   3. 示例三：跟踪代码依赖性，实现替代配置文件功能

3. 如何自定义注解：参照@SuppressWarnings定义

   1. 注解声明为：@interface

   2. 内部定义成员，通常使用value表示

   3. 可以指定成员的默认值，使用default定义

   4. 如果自定义注解没成员，表明是一个标识作用。

   5. 说明：

      - 如果注解有成员，在使用注解时，需要指明成员的值。
      - 自定义注解必须配上注解的信息处理流程(使用反射)才意义。
      - 自定义注解通过都会指明两个元注解：Retention、Target

   6. 代码举例：

      ```java
      @Inherited
      @Repeatable(MyAnnotations.class)
      @Retention(RetentionPolicy.RUNTIME)
      @Target({TYPE, FIELD, METHOD, PARAMETER, CONSTRUCTOR, LOCAL_VARIABLE,TYPE_PARAMETER,TYPE_USE})
      public @interface MyAnnotation {
      
          String value() default "hello";
      }
      ```

      

4. 元注解 ：对现有的注解进行解释说明的注解。

   jdk 提供的4种元注解：

   1. Retention：指定所修饰的 Annotation 的生命周期：SOURCE\CLASS（默认行为\RUNTIME
          只声明为RUNTIME生命周期的注解，才能通过反射获取。

   2. Target:用于指定被修饰的 Annotation 能用于修饰哪些程序元素

      *******出现的频率较低*******

   3. Documented:表示所修饰的注解在被javadoc解析时，保留下来。

   4. Inherited:被它修饰的 Annotation 将具继承性。

   --->类比：元数据的概念：String name = "Tom";

5. 如何获取注解信息:通过发射来进行获取、调用。

   前提：要求此注解的元注解Retention中声明的生命周期状态为：RUNTIME.

6. JDK8中注解的新特性：可重复注解、类型注解

   1. 可重复注解：
      1. 在MyAnnotation上声明@Repeatable，成员值为MyAnnotations.class

      2. MyAnnotation的Target和Retention等元注解与MyAnnotations相同。
   2. 类型注解：
      1. ElementType.TYPE_PARAMETER 表示该注解能写在类型变量的声明语句中（如：泛型声明。
      2. ElementType.TYPE_USE 表示该注解能写在使用类型的任何语句中。

## 三、Java集合

### 数组与集合

1. 集合与数组存储数据概述：
   1. 集合、数组都是对多个数据进行存储操作的结构，简称Java容器。
   2. 说明：此时的存储，主要指的是内存层面的存储，不涉及到持久化的存储（.txt,.jpg,.avi，数据库中)
2. 数组存储的特点：
   1. 一旦初始化以后，其长度就确定了。
   2. 数组一旦定义好，其元素的类型也就确定了。我们也就只能操作指定类型的数据了。
      *       比如：String[] arr;int[] arr1;Object[] arr2;
3. 数组存储的弊端：
   1. 一旦初始化以后，其长度就不可修改。
   2. 数组中提供的方法非常限，对于添加、删除、插入数据等操作，非常不便，同时效率不高。
   3. 获取数组中实际元素的个数的需求，数组没有现成的属性或方法可用
   4. 数组存储数据的特点：有序、可重复。对于无序、不可重复的需求，不能满足。
4. 集合存储的优点：解决数组存储数据方面的弊端。

### Collection接口

1. 单列集合框架结构

   ```java
   |----Collection接口：单列集合，用来存储一个一个的对象
   *          |----List接口：存储序的、可重复的数据。  -->“动态”数组
   *              |----ArrayList、LinkedList、Vector
   *
   *          |----Set接口：存储无序的、不可重复的数据   -->高中讲的“集合”
   *              |----HashSet、LinkedHashSet、TreeSet
   ```

   对应图示：

   ![image-20211129093716899](/blogs/_archive-2024-assets/42c792914d41d320c30c.webp)

2. Collection接口常用方法：

   ```java
   add(Object obj),addAll(Collection coll),size(),isEmpty(),clear();
   contains(Object obj),containsAll(Collection coll),remove(Object obj),removeAll(Collection coll),retainsAll(Collection coll),equals(Object obj);
   hasCode(),toArray(),iterator();
   ```

   

3. Collection集合与数组间的转换

   ```java
   //集合 --->数组：toArray()
   Object[] arr = coll.toArray();
   for(int i = 0;i < arr.length;i++){
       System.out.println(arr[i]);
   }
   
   //拓展：数组 --->集合:调用Arrays类的静态方法asList(T ... t)
   List<String> list = Arrays.asList(new String[]{"AA", "BB", "CC"});
   System.out.println(list);
   
   List arr1 = Arrays.asList(new int[]{123, 456});
   System.out.println(arr1.size());//1
   
   List arr2 = Arrays.asList(new Integer[]{123, 456});
   System.out.println(arr2.size());//2
   ```

   

4. 使用Collection集合存储对象，要求对象所属的类满足：向Collection接口的实现类的对象中添加数据obj时，要求obj所在类要重写equals().

5. 本章节对大家的要求：

   1. 层次一：选择合适的集合类去实现数据的保存，调用其内部的相关方法。
   2. 层次二：不同的集合类底层的数据结构为何？如何实现数据的操作的：增删改查等。

### Iterator接口与foreach循环 

1. 遍历Collection的两种方式：

   1. 使用迭代器Iterator  
   2. foreach循环（或增强for循环）

2. java.utils包下定义的迭代器接口：Iterator

   1. 说明：

      1. Iterator对象称为迭代器(设计模式的一种)，主要用于遍历 Collection 集合中的元素。
      2. GOF给迭代器模式的定义为：提供一种方法访问一个容器(container)对象中各个元素，而又不需暴露该对象的内部细节。迭代器模式，就是为容器而生。

   2. 作用：遍历集合Collectiton元素

   3. 如何获取实例：coll.iterator()返回一个迭代器实例

   4. 遍历的代码实现：

      ```java
      Iterator iterator = coll.iterator();
      //hasNext():判断是否还下一个元素
      while(iterator.hasNext()){
          //next():①指针下移 ②将下移以后集合位置上的元素返回
          System.out.println(iterator.next());
      }
      
      ```

      

   5. 图示说明：

      ![image-20211129093956649](/blogs/_archive-2024-assets/89dc005702b7c7d7eb78.webp)

   6. remove()的使用：

      ```java
      //测试Iterator中的remove()
      //如果还未调用next()或在上一次调用 next 方法之后已经调用了 remove 方法，再调用remove都会报IllegalStateException。
      //内部定义了remove(),可以在遍历的时候，删除集合中的元素。此方法不同于集合直接调用remove()
          @Test
          public void test3(){
              Collection coll = new ArrayList();
              coll.add(123);
              coll.add(456);
              coll.add(new Person("Jerry",20));
              coll.add(new String("Tom"));
              coll.add(false);
      
              //删除集合中"Tom"
              Iterator iterator = coll.iterator();
              while (iterator.hasNext()){
      //            iterator.remove();
                  Object obj = iterator.next();
                  if("Tom".equals(obj)){
                      iterator.remove();
      //                iterator.remove();
                  }
      
              }
              //遍历集合
              iterator = coll.iterator();
              while (iterator.hasNext()){
                  System.out.println(iterator.next());
              }
          }
      ```

      

3. jdk5.0新特性--增强for循环：(foreach循环)

   1. 遍历集合举例：

      ```java
      @Test
      public void test1(){
          Collection coll = new ArrayList();
          coll.add(123);
          coll.add(456);
          coll.add(new Person("Jerry",20));
          coll.add(new String("Tom"));
          coll.add(false);
      
          //for(集合元素的类型 局部变量 : 集合对象)
          
          for(Object obj : coll){
              System.out.println(obj);
          }
      }
      ```

      说明：
      内部仍然调用了迭代器。

   2. 遍历数组举例：

      ```java
      @Test
      public void test2(){
          int[] arr = new int[]{1,2,3,4,5,6};
          //for(数组元素的类型 局部变量 : 数组对象)
          for(int i : arr){
              System.out.println(i);
          }
      }
      ```

      

### Collection子接口：List接口

1. 存储的数据特点：存储序的、可重复的数据。

2. 常用方法：(记住)

   ```java
   增：add(Object obj)
   删：remove(int index) / remove(Object obj)
   改：set(int index, Object ele)
   查：get(int index)
   插：add(int index, Object ele)
   长度：size()
   遍历：① Iterator迭代器方式
        ② 增强for循环
        ③ 普通的循环
   ```

   

3. 常用实现类：

   ```java
   |----Collection接口：单列集合，用来存储一个一个的对象
    |----List接口：存储序的、可重复的数据。  -->“动态”数组,替换原的数组
     |----ArrayList：作为List接口的主要实现类；线程不安全，效率高；底层使用Object[]elementData存储
     |----LinkedList：对于频繁的插入、删除操作，使用此类效率比ArrayList高；底层使用双向链表存储
     |----Vector：作为List接口的古老实现类；线程安全的，效率低；底层使用Object[] elementData存储
   ```

   

4. 源码分析(难点)

   1. ArrayList的源码分析：

      1. jdk 7情况下

         ```java
         ArrayList list = new ArrayList();//底层创建了长度是10的Object[]数组elementData
         list.add(123);//elementData[0] = new Integer(123);
          ...
         list.add(11);//如果此次的添加导致底层elementData数组容量不够，则扩容。
         默认情况下，扩容为原来的容量的1.5倍，同时需要将原有数组中的数据复制到新的数组中。
         *
         结论：建议开发中使用带参的构造器：ArrayList list = new ArrayList(int capacity)
         ```

         

      2. jdk 8中ArrayList的变化：

         ```java
         ArrayList list = new ArrayList();//底层Object[] elementData初始化为{}.并没创建长度为10的数组
         *
         list.add(123);//第一次调用add()时，底层才创建了长度10的数组，并将数据123添加到elementData[0]
         *      ...
         后续的添加和扩容操作与jdk 7 无异。
         ```

         

      3. 小结：

         1. jdk7中的ArrayList的对象的创建类似于单例的饿汉式
         2. jdk8中的ArrayList的对象的创建类似于单例的懒汉式，延迟了数组的创建，节省内存。

   2. LinkedList的源码分析：

      ```java
      LinkedList list = new LinkedList(); 内部声明了Node类型的first和last属性，默认值为null
      list.add(123);//将123封装到Node中，创建了Node对象。
      
      其中，Node定义为：体现了LinkedList的双向链表的说法
      private static class Node<E> {
         E item;
         Node<E> next;
         Node<E> prev;
      
         Node(Node<E> prev, E element, Node<E> next) {
         this.item = element;
         this.next = next;
         his.prev = prev;
         }
      }
      ```

      

   3. Vector的源码分析：

      jdk7和jdk8中通过Vector()构造器创建对象时，底层都创建了长度为10的数组。
      在扩容方面，默认扩容为原来的数组长度的2倍。

5. 存储的元素的要求：添加的对象，所在的类要重写equals()方法

6. [面试题]ArrayList、LinkedList、Vector者的异同？

   1. 同：三个类都是实现了List接口，存储数据的特点相同：存储序的、可重复的数据
   2. 不同：见上

### Collection子接口：Set接口

1. 存储的数据特点：无序的、不可重复的元素

   具体的：以HashSet为例说明：

   1. 无序性：不等于随机性。存储的数据在底层数组中并非照数组索引的顺序添加，而是根据数据的哈希值决定的。
   2. 不可重复性：保证添加的元素照equals()判断时，不能返回true.即：相同的元素只能添加一个。

2. 元素添加过程：(以HashSet为例)

   ```txt
   我们向HashSet中添加元素a,首先调用元素a所在类的hashCode()方法，计算元素a的哈希值，
   此哈希值接着通过某种算法计算出在HashSet底层数组中的存放位置（即为：索引位置，判断
   数组此位置上是否已经元素：
       如果此位置上没其他元素，则元素a添加成功。 --->情况1
       如果此位置上其他元素b(或以链表形式存在的多个元素，则比较元素a与元素b的hash值：
           如果hash值不相同，则元素a添加成功。--->情况2
           如果hash值相同，进而需要调用元素a所在类的equals()方法：
                  equals()返回true,元素a添加失败
                  equals()返回false,则元素a添加成功。--->情况3
   
   对于添加成功的情况2和情况3而言：元素a 与已经存在指定索引位置上数据以链表的方式存储。
   jdk 7 :元素a放到数组中，指向原来的元素。
   jdk 8 :原来的元素在数组中，指向元素a
   总结：七上八下
   
   HashSet底层：数组+链表的结构。（前提：jdk7)
   ```

   

3. 常用方法：Set接口中没额外定义新的方法，使用的都是Collection中声明过的方法。

4. 常用实现类：

   ```java
   |----Collection接口：单列集合，用来存储一个一个的对象
   	|----Set接口：存储无序的、不可重复的数据   -->高中讲的“集合”
   		|----HashSet：作为Set接口的主要实现类；线程不安全的；可以存储null值
   		|----LinkedHashSet：作为HashSet的子类；遍历其内部数据时，可以按照添加的顺序遍历
                    在添加数据的同时，每个数据还维护了两个引用，记录此数据前一个数据和后一个数据。                   对于频繁的遍历操作，LinkedHashSet效率高于HashSet.
   		|----TreeSet：可以照添加对象的指定属性，进行排序。
   ```

   

5. 存储对象所在类的要求：

   HashSet/LinkedHashSet:

   ```
   要求：向Set(主要指：HashSet、LinkedHashSet)中添加的数据，其所在的类一定要重写hashCode()和equals()
   
   要求：重写的hashCode()和equals()尽可能保持一致性：相等的对象必须具有相等的散列码
   重写两个方法的小技巧：对象中用作 equals() 方法比较的 Field，都应该用来计算 hashCode 值。
   ```

   TreeSet:

   1. 自然排序中，比较两个对象是否相同的标准为：compareTo()返回0.不再是equals().
   2. 定制排序中，比较两个对象是否相同的标准为：compare()返回0.不再是equals().

6. TreeSet的使用

   1. 使用说明:

      1. 向TreeSet中添加的数据，要求是相同类的对象。
      2. 两种排序方式：自然排序（实现Comparable接口 和 定制排序（Comparator）

   2. 常用的排序方式:

      ```java
      //方式一：自然排序
      @Test
          public void test1(){
              TreeSet set = new TreeSet();
      
              //失败：不能添加不同类的对象
      //        set.add(123);
      //        set.add(456);
      //        set.add("AA");
      //        set.add(new User("Tom",12));
      
                  //举例一：
      //        set.add(34);
      //        set.add(-34);
      //        set.add(43);
      //        set.add(11);
      //        set.add(8);
      
              //举例二：
              set.add(new User("Tom",12));
              set.add(new User("Jerry",32));
              set.add(new User("Jim",2));
              set.add(new User("Mike",65));
              set.add(new User("Jack",33));
              set.add(new User("Jack",56));
      
      
              Iterator iterator = set.iterator();
              while(iterator.hasNext()){
                  System.out.println(iterator.next());
              }
      
          }
      
      //方式二：定制排序
          @Test
          public void test2(){
              Comparator com = new Comparator() {
                  //照年龄从小到大排列
                  @Override
                  public int compare(Object o1, Object o2) {
                      if(o1 instanceof User && o2 instanceof User){
                          User u1 = (User)o1;
                          User u2 = (User)o2;
                          return Integer.compare(u1.getAge(),u2.getAge());
                      }else{
                          throw new RuntimeException("输入的数据类型不匹配");
                      }
                  }
              };
      
              TreeSet set = new TreeSet(com);
              set.add(new User("Tom",12));
              set.add(new User("Jerry",32));
              set.add(new User("Jim",2));
              set.add(new User("Mike",65));
              set.add(new User("Mary",33));
              set.add(new User("Jack",33));
              set.add(new User("Jack",56));
      
      
              Iterator iterator = set.iterator();
              while(iterator.hasNext()){
                  System.out.println(iterator.next());
              }
          }
      
      
      
      ```

      

### Map接口

双列集合框架：Map

1. 常用实现类结构

   ```java
   |----Map:双列数据，存储key-value对的数据   ---类似于高中的函数：y = f(x)
   	|----HashMap:作为Map的主要实现类；线程不安全的，效率高；存储null的key和value
   		|----LinkedHashMap:保证在遍历map元素时，可以按照添加的顺序实现遍历。
                 原因：在原有的HashMap底层结构基础上，添加了一对指针，指向前一个和后一个元素。
                 对于频繁的遍历操作，此类执行效率高于HashMap。
   		|----TreeMap:保证按照添加的key-value对进行排序，实现排序遍历。此时考虑key的自然或定制排序
   					底层使用红黑树
   		|----Hashtable:作为古老的实现类；线程安全的，效率低；不能存储null的key和value
   			|----Properties:常用来处理配置文件。key和value都是String类型
   ```

   HashMap的底层：数组+链表  （jdk7及之前)

   ​								数组+链表+红黑树 （jdk 8)

   [面试题]

   1. HashMap的底层实现原理？
   2. HashMap 和 Hashtable的异同？
   3. CurrentHashMap 与 Hashtable的异同？（暂时不讲)

2. 存储结构的理解：

   1. Map中的key:无序的、不可重复的，使用Set存储所的key  ---> key所在的类要重写equals()和hashCode() （以HashMap为例)

   2. Map中的value:无序的、可重复的，使用Collection存储所有的value

      value所在的类要重写equals()

   3. 一个键值对：key-value构成了一个Entry对象。

   4. Map中的entry:无序的、不可重复的，使用Set存储所的entry

      图示：

      ![image-20211129101834318](/blogs/_archive-2024-assets/1056771a298ae77c4b11.webp)

3. 常用方法

   ```java
   * 添加：put(Object key,Object value)
   * 删除：remove(Object key)
   * 修改：put(Object key,Object value)
   * 查询：get(Object key)
   * 长度：size()
   * 遍历：keySet() / values() / entrySet()
   ```

   

4. 内存结构说明：（难点）

   1. HashMap在jdk7中实现原理：

      ```txt
      HashMap map = new HashMap():
      在实例化以后，底层创建了长度是16的一维数组Entry[] table。
      ...可能已经执行过多次put...
      map.put(key1,value1):首先，调用key1所在类的hashCode()计算key1哈希值，此哈希值经过某种算法计算以后，得到在Entry数组中的存放位置。
      	如果此位置上的数据为空，此时的key1-value1添加成功。 ----情况1
      	如果此位置上的数据不为空，(意味着此位置上存在一个或多个数据(以链表形式存在)),比较key1和已经存在的一个或多个数据的哈希值：
      		如果key1的哈希值与已经存在的数据的哈希值都不相同，此时key1-value1添加成功。----情况2
      		如果key1的哈希值和已经存在的某一个数据(key2-value2)的哈希值相同，继续比较：调用key1所在类的equals(key2)方法，比较：
      			如果equals()返回false:此时key1-value1添加成功。----情况3
      			如果equals()返回true:使用value1替换value2。
      
      补充：关于情况2和情况3：此时key1-value1和原来的数据以链表的方式存储。
      
      在不断的添加过程中，会涉及到扩容问题，当超出临界值(且要存放的位置非空)时，扩容。默认的扩容方式：扩容为原来容量的2倍，并将原的数据复制过来。
      ```

      

   2. HashMap在jdk8中相较于jdk7在底层实现方面的不同：

      1. new HashMap():底层没创建一个长度为16的数组
      2. jdk 8底层的数组是：Node[],而非Entry[]
      3. 首次调用put()方法时，底层创建长度为16的数组
      4. jdk7底层结构只有：数组+链表。jdk8中底层结构：数组+链表+红黑树。
        5. 形成链表时，七上八下（jdk7:新的元素指向旧的元素。jdk8：旧的元素指向新的元素）
        6. 当数组的某一个索引位置上的元素以链表形式存在的数据个数 > 8 且当前数组的长度 > 64时，此时此索引位置上的所数据改为使用红黑树存储。

   3. HashMap底层典型属性的属性的说明：

      1. DEFAULT_INITIAL_CAPACITY : HashMap的默认容量，16
      2. DEFAULT_LOAD_FACTOR：HashMap的默认加载因子：0.75
      3. threshold：扩容的临界值，=容量*填充因子：16 * 0.75 => 12
      4. TREEIFY_THRESHOLD：Bucket中链表长度大于该默认值，转化为红黑树:8
      5. MIN_TREEIFY_CAPACITY：桶中的Node被树化时最小的hash表容量:64

   4. LinkedHashMap的底层实现原理(了解)

      1. LinkedHashMap底层使用的结构与HashMap相同，因为LinkedHashMap继承于HashMap.

      2. 区别就在于：LinkedHashMap内部提供了Entry，替换HashMap中的Node.

         ![image-20211129102303272](/blogs/_archive-2024-assets/4e33d4e8de0137e231ce.webp)

5. TreeMap的使用

   1. 向TreeMap中添加key-value，要求key必须是由同一个类创建的对象
   2. 因为要照key进行排序：自然排序 、定制排序

6. 使用Properties读取配置文件

   ```java
   //Properties:常用来处理配置文件。key和value都是String类型
   public static void main(String[] args)  {
       FileInputStream fis = null;
       try {
           Properties pros = new Properties();
   
           fis = new FileInputStream("jdbc.properties");
           pros.load(fis);//加载流对应的文件
   
           String name = pros.getProperty("name");
           String password = pros.getProperty("password");
   
           System.out.println("name = " + name + ", password = " + password);
       } catch (IOException e) {
           e.printStackTrace();
       } finally {
           if(fis != null){
               try {
                   fis.close();
               } catch (IOException e) {
                   e.printStackTrace();
               }
   
           }
       }
   
   ```

   

### Collections工具类的使用

1. 作用：操作Collection和Map的工具类

2. 常用方法：

   ```java
   reverse(List)：反转 List 中元素的顺序
   shuffle(List)：对 List 集合元素进行随机排序
   sort(List)：根据元素的自然顺序对指定 List 集合元素升序排序
   sort(List，Comparator)：根据指定的 Comparator 产生的顺序对 List 集合元素进行排序
   swap(List，int， int)：将指定 list 集合中的 i 处元素和 j 处元素进行交换
   Object max(Collection)：根据元素的自然顺序，返回给定集合中的最大元素
   Object max(Collection，Comparator)：根据 Comparator 指定的顺序，返回给定集合中的最大元素
   Object min(Collection)
   Object min(Collection，Comparator)
   int frequency(Collection，Object)：返回指定集合中指定元素的出现次数
   void copy(List dest,List src)：将src中的内容复制到dest中
   boolean replaceAll(List list，Object oldVal，Object newVal)：使用新值替换 List 对象的所旧值
   ```

   ![image-20211129102433478](/blogs/_archive-2024-assets/a257e3a43225ed4ee17e.webp)

   说明：ArrayList和HashMap都是线程不安全的，如果程序要求线程安全，我们可以将ArrayList、HashMap转换为线程的。
   使用synchronizedList(List list） 和 synchronizedMap(Map map）

3. 面试题：Collection 和 Collections的区别？

### 数据结构简述

1. 数据结构概述

   数据结构（Data Structure是一门和计算机硬件与软件都密切相关的学科，它的研究重点是在计算机的程序设计领域中探讨如何在计算机中组织和存储数据并进行高效率的运用，**涉及的内容包含：数据的逻辑关系、数据的存储结构、排序算法（Algorithm）、查找（或搜索）等。**

2. 数据结构与算法的理解

   程序能否快速而高效地完成预定的任务，取决于是否选对了数据结构，而程序是否能清楚而正确地把问题解决，则取决于算法。

   所以大家认为：“Algorithms + Data Structures = Programs”（出自：Pascal之父Nicklaus Wirth）

   总结：**算法是为了解决实际问题而设计的，数据结构是算法需要处理的问题载体。**

3. 数据结构的研究对象

   1. 数据间的逻辑结构

      ![image-20211129102620506](/blogs/_archive-2024-assets/c9991d1d5bd39ea9a813.webp)

      ![image-20211129102630361](/blogs/_archive-2024-assets/09f06b5736a51a3bdbc5.webp)

      ​    集合结构            一对一：线性结构

      ![image-20211129102644497](/blogs/_archive-2024-assets/967548f8f9780f293f48.webp)

      ![image-20211129102648930](/blogs/_archive-2024-assets/d2f916915c8b07233412.webp)

      一对多：树形结构      多对多：图形结构

   2. 数据的存储结构：

      1. 线性表（顺序表、链表、栈、队列）

      2. 树

      3. 图

         说明：

         1. 习惯上把顺序表和链表看做基本数据结构（或真实数据结构）

         2. 习惯上把栈、队列、树、图看做抽象数据类型，简称ADT

      

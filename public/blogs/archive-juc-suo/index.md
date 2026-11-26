# 一、**锁**

## 一、**锁的分类**

### 1.1 可重入锁、不可重入锁

Java中提供的synchronized，ReentrantLock，ReentrantReadWriteLock都是可重入锁。

**重入**：当前线程获取到A锁，在获取之后尝试再次获取A锁是可以直接拿到的。

**不可重入**：当前线程获取到A锁，在获取之后尝试再次获取A锁，无法获取到的，因为A锁被当前线程占用着，需要等待自己释放锁再获取锁。

### 1.2 乐观锁、悲观锁

Java中提供的synchronized，ReentrantLock，ReentrantReadWriteLock都是悲观锁。

Java中提供的CAS操作，就是乐观锁的一种实现。

**悲观锁**：获取不到锁资源时，会将当前线程挂起（进入BLOCKED、WAITING），线程挂起会涉及到用户态和内核的太的切换，而这种切换是比较消耗资源的。

* 用户态：JVM可以自行执行的指令，不需要借助操作系统执行。
* 内核态：JVM不可以自行执行，需要操作系统才可以执行。

**乐观锁**：获取不到锁资源，可以再次让CPU调度，重新尝试获取锁资源。

Atomic原子性类中，就是基于CAS乐观锁实现的。

### 1.3 公平锁、非公平锁

Java中提供的synchronized只能是非公平锁。

Java中提供的ReentrantLock，ReentrantReadWriteLock可以实现公平锁和非公平锁

**公平锁**：线程A获取到了锁资源，线程B没有拿到，线程B去排队，线程C来了，锁被A持有，同时线程B在排队。直接排到B的后面，等待B拿到锁资源或者是B取消后，才可以尝试去竞争锁资源。

**非公平锁**：线程A获取到了锁资源，线程B没有拿到，线程B去排队，线程C来了，先尝试竞争一波

* 拿到锁资源：开心，插队成功。
* 没有拿到锁资源：依然要排到B的后面，等待B拿到锁资源或者是B取消后，才可以尝试去竞争锁资源。

### 1.4 互斥锁、共享锁

Java中提供的synchronized、ReentrantLock是互斥锁。

Java中提供的ReentrantReadWriteLock，有互斥锁也有共享锁。

**互斥锁**：同一时间点，只会有一个线程持有者当前互斥锁。

**共享锁**：同一时间点，当前共享锁可以被多个线程同时持有。

## 二、**深入synchronized**

### 2.1 类锁、对象锁

synchronized的使用一般就是同步方法和同步代码块。

synchronized的锁是基于对象实现的。

如果使用同步方法

* static：此时使用的是当前类.class作为锁（类锁）

* 非static：此时使用的是当前对象做为锁（对象锁）

  ```java
  public class MiTest {
  
      public static void main(String[] args) {
          // 锁的是，当前Test.class
          Test.a();
  
          Test test = new Test();
          // 锁的是new出来的test对象
          test.b();
      }
  
  }
  
  class Test{
      public static synchronized void a(){
          System.out.println("1111");
      }
  
      public synchronized void b(){
          System.out.println("2222");
      }
  }
  ```

### 2.2 synchronized的优化

在JDK1.5的时候，Doug Lee推出了ReentrantLock，lock的性能远高于synchronized，所以JDK团队就在JDK1.6中，对synchronized做了大量的优化。

**锁消除**：在synchronized修饰的代码中，如果不存在操作临界资源的情况，会触发锁消除，你即便写了synchronized，他也不会触发。

```java
public synchronized void method(){
    // 没有操作临界资源
    // 此时这个方法的synchronized你可以认为木有~~
}
```

**锁膨胀**：如果在一个循环中，频繁的获取和释放做资源，这样带来的消耗很大，锁膨胀就是将锁的范围扩大，避免频繁的竞争和获取锁资源带来不必要的消耗。

```java
public void method(){
    for(int i = 0;i < 999999;i++){
        synchronized(对象){

        }
    }
    // 这是上面的代码会触发锁膨胀
    synchronized(对象){
        for(int i = 0;i < 999999;i++){

        }
    }
}
```

**锁升级**：ReentrantLock的实现，是先基于乐观锁的CAS尝试获取锁资源，如果拿不到锁资源，才会挂起线程。synchronized在JDK1.6之前，完全就是获取不到锁，立即挂起当前线程，所以synchronized性能比较差。

synchronized就在JDK1.6做了锁升级的优化

* **无锁、匿名偏向**：当前对象没有作为锁存在。
* **偏向锁**：如果当前锁资源，只有一个线程在频繁的获取和释放，那么这个线程过来，只需要判断，当前指向的线程是否是当前线程 。
  * 如果是，直接拿着锁资源走。
  * 如果当前线程不是我，基于CAS的方式，尝试将偏向锁指向当前线程。如果获取不到，触发锁升级，升级为轻量级锁。（偏向锁状态出现了锁竞争的情况）
* **轻量级锁**：会采用自旋锁的方式去频繁的以CAS的形式获取锁资源（采用的是**自适应自旋锁**）
  * 如果成功获取到，拿着锁资源走
  * 如果自旋了一定次数，没拿到锁资源，锁升级。
* **重量级锁**：就是最传统的synchronized方式，拿不到锁资源，就挂起当前线程。（用户态&内核态）

### 2.3 synchronized实现原理

synchronized是基于对象实现的。

先要对Java中对象在堆内存的存储有一个了解。

![image.png](/blogs/_archive-2024-assets/bc05170f4b060b559e88.webp)

展开MarkWord

![](https://gimg2.baidu.com/image_search/src=http%3A%2F%2Fimg-blog.csdnimg.cn%2F20200314202610433.png%3Fx-oss-process%3Dimage%2Fwatermark%2Ctype_ZmFuZ3poZW5naGVpdGk%2Cshadow_10%2Ctext_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L0ludHJvbmNoZW5n%2Csize_16%2Ccolor_FFFFFF%2Ct_70&refer=http%3A%2F%2Fimg-blog.csdnimg.cn&app=2002&size=f9999,10000&q=a80&n=0&g=0n&fmt=auto?sec=1659024071&t=5135a8e6d07b807c6bb771ceafd8a227)

MarkWord中标记着四种锁的信息：无锁、偏向锁、轻量级锁、

### 2.4 synchronized的锁升级

为了可以在Java中看到对象头的MarkWord信息，需要导入依赖

```xml
<dependency>
    <groupId>org.openjdk.jol</groupId>
    <artifactId>jol-core</artifactId>
    <version>0.9</version>
</dependency>
```

锁默认情况下，开启了偏向锁延迟。

> 偏向锁在升级为轻量级锁时，会涉及到偏向锁撤销，需要等到一个安全点（STW），才可以做偏向锁撤销，在明知道有并发情况，就可以选择不开启偏向锁，或者是设置偏向锁延迟开启
>
> 因为JVM在启动时，需要加载大量的.class文件到内存中，这个操作会涉及到synchronized的使用，为了避免出现偏向锁撤销操作，JVM启动初期，有一个延迟4s开启偏向锁的操作
>
> 如果正常开启偏向锁了，那么不会出现无锁状态，对象会直接变为匿名偏向

```java
public static void main(String[] args) throws InterruptedException {
    Thread.sleep(5000);
    Object o = new Object();
    System.out.println(ClassLayout.parseInstance(o).toPrintable());

    new Thread(() -> {

        synchronized (o){
            //t1  - 偏向锁
            System.out.println("t1:" + ClassLayout.parseInstance(o).toPrintable());
        }
    }).start();
    //main - 偏向锁 - 轻量级锁CAS - 重量级锁
    synchronized (o){
        System.out.println("main:" + ClassLayout.parseInstance(o).toPrintable());
    }
}
```

整个锁升级状态的转变：

![image.png](/blogs/_archive-2024-assets/09b6dd9152a633588c7f.webp)

Lock Record以及ObjectMonitor存储的内容

![image.png](/blogs/_archive-2024-assets/f1c89067f3ffdea2ab8d.webp)

### 2.5 重量锁底层ObjectMonitor

需要去找到openjdk，在百度中直接搜索openjdk，第一个链接就是

找到ObjectMonitor的两个文件，hpp，cpp

先查看核心属性：http://hg.openjdk.java.net/jdk8u/jdk8u/hotspot/file/69087d08d473/src/share/vm/runtime/objectMonitor.hpp

```hpp
ObjectMonitor() {
    _header       = NULL;   // header存储着MarkWord
    _count        = 0;      // 竞争锁的线程个数
    _waiters      = 0,      // wait的线程个数
    _recursions   = 0;      // 标识当前synchronized锁重入的次数
    _object       = NULL;
    _owner        = NULL;   // 持有锁的线程
    _WaitSet      = NULL;   // 保存wait的线程信息，双向链表
    _WaitSetLock  = 0 ;
    _Responsible  = NULL ;
    _succ         = NULL ;
    _cxq          = NULL ;  // 获取锁资源失败后，线程要放到当前的单向链表中
    FreeNext      = NULL ;
    _EntryList    = NULL ;  // _cxq以及被唤醒的WaitSet中的线程，在一定机制下，会放到EntryList中
    _SpinFreq     = 0 ;
    _SpinClock    = 0 ;
    OwnerIsThread = 0 ;
    _previous_owner_tid = 0;
  }
```

适当的查看几个C++中实现的加锁流程

http://hg.openjdk.java.net/jdk8u/jdk8u/hotspot/file/69087d08d473/src/share/vm/runtime/objectMonitor.cpp

TryLock

```cpp
int ObjectMonitor::TryLock (Thread * Self) {
   for (;;) {
	  // 拿到持有锁的线程
      void * own = _owner ;
      // 如果有线程持有锁，告辞
      if (own != NULL) return 0 ;
      // 说明没有线程持有锁，own是null，cmpxchg指令就是底层的CAS实现。
      if (Atomic::cmpxchg_ptr (Self, &_owner, NULL) == NULL) {
		 // 成功获取锁资源
         return 1 ;
      }
      // 这里其实重试操作没什么意义，直接返回-1
      if (true) return -1 ;
   }
}
```

try_entry

```cpp
bool ObjectMonitor::try_enter(Thread* THREAD) {
  // 在判断_owner是不是当前线程
  if (THREAD != _owner) {
    // 判断当前持有锁的线程是否是当前线程，说明轻量级锁刚刚升级过来的情况
    if (THREAD->is_lock_owned ((address)_owner)) {
       _owner = THREAD ;
       _recursions = 1 ;
       OwnerIsThread = 1 ;
       return true;
    }
    // CAS操作，尝试获取锁资源
    if (Atomic::cmpxchg_ptr (THREAD, &_owner, NULL) != NULL) {
      // 没拿到锁资源，告辞
      return false;
    }
    // 拿到锁资源
    return true;
  } else {
    // 将_recursions + 1，代表锁重入操作。
    _recursions++;
    return true;
  }
}
```

enter（想方设法拿到锁资源，如果没拿到，挂起扔到_cxq单向链表中）

```cpp
void ATTR ObjectMonitor::enter(TRAPS) {
  // 拿到当前线程
  Thread * const Self = THREAD ;
  void * cur ;
  // CAS走你，
  cur = Atomic::cmpxchg_ptr (Self, &_owner, NULL) ;
  if (cur == NULL) {
     // 拿锁成功
     return ;
  }
  // 锁重入操作
  if (cur == Self) {
     // TODO-FIXME: check for integer overflow!  BUGID 6557169.
     _recursions ++ ;
     return ;
  }
  //轻量级锁过来的。
  if (Self->is_lock_owned ((address)cur)) {
    _recursions = 1 ;
    _owner = Self ;
    OwnerIsThread = 1 ;
    return ;
  }


  // 走到这了，没拿到锁资源，count++
  Atomic::inc_ptr(&_count);

  
    for (;;) {
      jt->set_suspend_equivalent();
      // 入队操作，进到cxq中
      EnterI (THREAD) ;
      if (!ExitSuspendEquivalent(jt)) break ;
      _recursions = 0 ;
      _succ = NULL ;
      exit (false, Self) ;
      jt->java_suspend_self();
    }
  }
  // count--
  Atomic::dec_ptr(&_count);
  
}
```

EnterI

```cpp
for (;;) {
    // 入队
    node._next = nxt = _cxq ;
    // CAS的方式入队。
    if (Atomic::cmpxchg_ptr (&node, &_cxq, nxt) == nxt) break ;

    // 重新尝试获取锁资源
    if (TryLock (Self) > 0) {
        assert (_succ != Self         , "invariant") ;
        assert (_owner == Self        , "invariant") ;
        assert (_Responsible != Self  , "invariant") ;
        return ;
    }
}
```

## 三、**深入ReentrantLock**

### 3.1 ReentrantLock和synchronized的区别

废话区别：单词不一样。。。

核心区别：

* ReentrantLock是个类，synchronized是关键字，当然都是在JVM层面实现互斥锁的方式

效率区别：

* 如果竞争比较激烈，推荐ReentrantLock去实现，不存在锁升级概念。而synchronized是存在锁升级概念的，如果升级到重量级锁，是不存在锁降级的。

底层实现区别：

* 实现原理是不一样，ReentrantLock基于AQS实现的，synchronized是基于ObjectMonitor

功能向的区别：

* ReentrantLock的功能比synchronized更全面。
  * ReentrantLock支持公平锁和非公平锁
  * ReentrantLock可以指定等待锁资源的时间。

选择哪个：如果你对并发编程特别熟练，推荐使用ReentrantLock，功能更丰富。如果掌握的一般般，使用synchronized会更好

### 3.2 AQS概述

AQS就是AbstractQueuedSynchronizer抽象类，AQS其实就是JUC包下的一个基类，JUC下的很多内容都是基于AQS实现了部分功能，比如ReentrantLock，ThreadPoolExecutor，阻塞队列，CountDownLatch，Semaphore，CyclicBarrier等等都是基于AQS实现。

首先AQS中提供了一个由volatile修饰，并且采用CAS方式修改的int类型的state变量。

其次AQS中维护了一个双向链表，有head，有tail，并且每个节点都是Node对象

```java
static final class Node {
        static final Node SHARED = new Node();
        static final Node EXCLUSIVE = null;

        static final int CANCELLED =  1;
        static final int SIGNAL    = -1;
        static final int CONDITION = -2;

        static final int PROPAGATE = -3;


        volatile int waitStatus;


        volatile Node prev;


        volatile Node next;


        volatile Thread thread; 
}
```

AQS内部结构和属性

![image.png](/blogs/_archive-2024-assets/66c82abf10c51e5bc768.webp)

### 3.3 加锁流程源码剖析

#### 3.3.1 加锁流程概述

这个是非公平锁的流程

![image.png](/blogs/_archive-2024-assets/f3650a8155acc6d866ed.webp)

#### 3.3.2 三种加锁源码分析

##### 3.3.2.1 lock方法

1. 执行lock方法后，公平锁和非公平锁的执行套路不一样

   ```java
   // 非公平锁
   final void lock() {
       // 上来就先基于CAS的方式，尝试将state从0改为1
       if (compareAndSetState(0, 1))
           // 获取锁资源成功，会将当前线程设置到exclusiveOwnerThread属性，代表是当前线程持有着锁资源
           setExclusiveOwnerThread(Thread.currentThread());
       else
           // 执行acquire，尝试获取锁资源
           acquire(1);
   }
   
   // 公平锁
   final void lock() {
       //  执行acquire，尝试获取锁资源
       acquire(1);
   }
   ```

2. acquire方法，是公平锁和非公平锁的逻辑一样

   ```java
   public final void acquire(int arg) {
       // tryAcquire：再次查看，当前线程是否可以尝试获取锁资源
       if (!tryAcquire(arg) &&
           // 没有拿到锁资源
           // addWaiter(Node.EXCLUSIVE)：将当前线程封装为Node节点，插入到AQS的双向链表的结尾
           // acquireQueued：查看我是否是第一个排队的节点，如果是可以再次尝试获取锁资源，如果长时间拿不到，挂起线程
           // 如果不是第一个排队的额节点，就尝试挂起线程即可
           acquireQueued(addWaiter(Node.EXCLUSIVE), arg))
           // 中断线程的操作
           selfInterrupt();
   }
   ```

3. tryAcquire方法竞争锁最资源的逻辑，分为公平锁和非公平锁

   ```java
   // 非公平锁实现
   final boolean nonfairTryAcquire(int acquires) {
       // 获取当前线程
       final Thread current = Thread.currentThread();
       // 获取了state熟属性
       int c = getState();
       // 判断state当前是否为0,之前持有锁的线程释放了锁资源
       if (c == 0) {
           // 再次抢一波锁资源
           if (compareAndSetState(0, acquires)) {
               setExclusiveOwnerThread(current);
               // 拿锁成功返回true
               return true;
           }
       }
       // 不是0，有线程持有着锁资源，如果是，证明是锁重入操作
       else if (current == getExclusiveOwnerThread()) {
           // 将state + 1
           int nextc = c + acquires;
           if (nextc < 0) // 说明对重入次数+1后，超过了int正数的取值范围
               // 01111111 11111111 11111111 11111111
               // 10000000 00000000 00000000 00000000
               // 说明重入的次数超过界限了。
               throw new Error("Maximum lock count exceeded");
           // 正常的将计算结果，复制给state
           setState(nextc);
           // 锁重入成功
           return true;
       }
       // 返回false
       return false;
   }
   ```


   // 公平锁实现
   protected final boolean tryAcquire(int acquires) {
       // 获取当前线程
       final Thread current = Thread.currentThread();
       // ....
       int c = getState();
       if (c == 0) {
           // 查看AQS中是否有排队的Node
           // 没人排队抢一手 。有人排队，如果我是第一个，也抢一手
           if (!hasQueuedPredecessors() &&
               // 抢一手~
               compareAndSetState(0, acquires)) {
               setExclusiveOwnerThread(current);
               return true;
           }
       }
       // 锁重入~~~
       else if (current == getExclusiveOwnerThread()) {
           int nextc = c + acquires;
           if (nextc < 0)
               throw new Error("Maximum lock count exceeded");
           setState(nextc);
           return true;
       }
       return false;
   }

   // 查看是否有线程在AQS的双向队列中排队
   // 返回false，代表没人排队
   public final boolean hasQueuedPredecessors() {
       // 头尾节点
       Node t = tail; 
       Node h = head;
       // s为头结点的next节点
       Node s;
       // 如果头尾节点相等，证明没有线程排队，直接去抢占锁资源
       return h != t &&
           // s节点不为null，并且s节点的线程为当前线程（排在第一名的是不是我）
           (s == null || s.thread != Thread.currentThread());
   }

   ```
4. addWaite方法，将没有拿到锁资源的线程扔到AQS队列中去排队
   ```java
   // 没有拿到锁资源，过来排队，  mode：代表互斥锁
   private Node addWaiter(Node mode) {
       // 将当前线程封装为Node，
       Node node = new Node(Thread.currentThread(), mode);
       // 拿到尾结点
       Node pred = tail;
       // 如果尾结点不为null
       if (pred != null) {
           // 当前节点的prev指向尾结点
           node.prev = pred;
           // 以CAS的方式，将当前线程设置为tail节点
           if (compareAndSetTail(pred, node)) {
               // 将之前的尾结点的next指向当前节点
               pred.next = node;
               return node;
           }
       }
       // 如果CAS失败，以死循环的方式，保证当前线程的Node一定可以放到AQS队列的末尾
       enq(node);
       return node;
   }

   private Node enq(final Node node) {
       for (;;) {
           // 拿到尾结点
           Node t = tail;
           // 如果尾结点为空，AQS中一个节点都没有，构建一个伪节点，作为head和tail
           if (t == null) { 
               if (compareAndSetHead(new Node()))
                   tail = head;
           } else {
               // 比较熟悉了，以CAS的方式，在AQS中有节点后，插入到AQS队列的末尾
               node.prev = t;
               if (compareAndSetTail(t, node)) {
                   t.next = node;
                   return t;
               }
           }
       }
   }
   ```

5. acquireQueued方法，判断当前线程是否还能再次尝试获取锁资源，如果不能再次获取锁资源，或者又没获取到，尝试将当前线程挂起

   ```java
   // 当前没有拿到锁资源后，并且到AQS排队了之后触发的方法。  中断操作这里不用考虑
   final boolean acquireQueued(final Node node, int arg) {
       // 不考虑中断
       // failed：获取锁资源是否失败（这里简单掌握落地，真正触发的，还是tryLock和lockInterruptibly）
       boolean failed = true;
       try {
           boolean interrupted = false;
           // 死循环…………
           for (;;) {
               // 拿到当前节点的前继节点
               final Node p = node.predecessor();
               // 前继节点是否是head，如果是head，再次执行tryAcquire尝试获取锁资源。
               if (p == head && tryAcquire(arg)) {
                   // 获取锁资源成功
                   // 设置头结点为当前获取锁资源成功Node，并且取消thread信息
                   setHead(node);
                   // help GC
                   p.next = null; 
                   // 获取锁失败标识为false
                   failed = false;
                   return interrupted;
               }
               // 没拿到锁资源……
               // shouldParkAfterFailedAcquire：基于上一个节点转改来判断当前节点是否能够挂起线程，如果可以返回true，
               // 如果不能，就返回false，继续下次循环
               if (shouldParkAfterFailedAcquire(p, node) &&
                   // 这里基于Unsafe类的park方法，将当前线程挂起
                   parkAndCheckInterrupt())
                   interrupted = true;
           }
       } finally {
           if (failed)
               // 在lock方法中，基本不会执行。
               cancelAcquire(node);
       }
   }
   // 获取锁资源成功后，先执行setHead
   private void setHead(Node node) {
       // 当前节点作为头结点  伪
       head = node;
       // 头结点不需要线程信息
       node.thread = null;
       node.prev = null;
   }
   
   // 当前Node没有拿到锁资源，或者没有资格竞争锁资源，看一下能否挂起当前线程
   private static boolean shouldParkAfterFailedAcquire(Node pred, Node node) {
       // -1，SIGNAL状态：代表当前节点的后继节点，可以挂起线程，后续我会唤醒我的后继节点
       // 1，CANCELLED状态：代表当前节点以及取消了
       int ws = pred.waitStatus;
       if (ws == Node.SIGNAL)
           // 上一个节点为-1之后，当前节点才可以安心的挂起线程
           return true;
       if (ws > 0) {
           // 如果当前节点的上一个节点是取消状态，我需要往前找到一个状态不为1的Node，作为他的next节点
           // 找到状态不为1的节点后，设置一下next和prev
           do {
               node.prev = pred = pred.prev;
           } while (pred.waitStatus > 0);
           pred.next = node;
       } else {
           // 上一个节点的状态不是1或者-1，那就代表节点状态正常，将上一个节点的状态改为-1
           compareAndSetWaitStatus(pred, ws, Node.SIGNAL);
       }
       return false;
   }
   ```

##### 3.3.2.2 tryLock方法

* tryLock();

  ```java
  // tryLock方法，无论公平锁还有非公平锁。都会走非公平锁抢占锁资源的操作
  // 就是拿到state的值， 如果是0，直接CAS浅尝一下
  // state 不是0，那就看下是不是锁重入操作
  // 如果没抢到，或者不是锁重入操作，告辞，返回false
  public boolean tryLock() {
      // 非公平锁的竞争锁操作
      return sync.nonfairTryAcquire(1);
  }
  final boolean nonfairTryAcquire(int acquires) {
      final Thread current = Thread.currentThread();
      int c = getState();
      if (c == 0) {
          if (compareAndSetState(0, acquires)) {
              setExclusiveOwnerThread(current);
              return true;
          }
      }
      else if (current == getExclusiveOwnerThread()) {
          int nextc = c + acquires;
          if (nextc < 0) // overflow
              throw new Error("Maximum lock count exceeded");
          setState(nextc);
          return true;
      }
      return false;
  }
  ```

* tryLock(time,unit);

  * 第一波分析，类似的代码：

    ```java
    // tryLock(time,unit)执行的方法
    public final boolean tryAcquireNanos(int arg, long nanosTimeout)throws InterruptedException {
        // 线程的中断标记位，是不是从false，别改为了true，如果是，直接抛异常
        if (Thread.interrupted())
            throw new InterruptedException();
        // tryAcquire分为公平和非公平锁两种执行方式，如果拿锁成功， 直接告辞，
        return tryAcquire(arg) ||
            // 如果拿锁失败，在这要等待指定时间
            doAcquireNanos(arg, nanosTimeout);
    }
    
    private boolean doAcquireNanos(int arg, long nanosTimeout)
            throws InterruptedException {
        // 如果等待时间是0秒，直接告辞，拿锁失败  
        if (nanosTimeout <= 0L)
            return false;
        // 设置结束时间。
        final long deadline = System.nanoTime() + nanosTimeout;
        // 先扔到AQS队列
        final Node node = addWaiter(Node.EXCLUSIVE);
        // 拿锁失败，默认true
        boolean failed = true;
        try {
            for (;;) {
                // 如果在AQS中，当前node是head的next，直接抢锁
                final Node p = node.predecessor();
                if (p == head && tryAcquire(arg)) {
                    setHead(node);
                    p.next = null; // help GC
                    failed = false;
                    return true;
                }
                // 结算剩余的可用时间
                nanosTimeout = deadline - System.nanoTime();
                // 判断是否是否用尽的位置
                if (nanosTimeout <= 0L)
                    return false;
                // shouldParkAfterFailedAcquire：根据上一个节点来确定现在是否可以挂起线程
                if (shouldParkAfterFailedAcquire(p, node) &&
                    // 避免剩余时间太少，如果剩余时间少就不用挂起线程
                    nanosTimeout > spinForTimeoutThreshold)
                    // 如果剩余时间足够，将线程挂起剩余时间
                    LockSupport.parkNanos(this, nanosTimeout);
                // 如果线程醒了，查看是中断唤醒的，还是时间到了唤醒的。
                if (Thread.interrupted())
                    // 是中断唤醒的！
                    throw new InterruptedException();
            }
        } finally {
            if (failed)
                cancelAcquire(node);
        }
    }
    ```

  * 取消节点分析：![image.png](/blogs/_archive-2024-assets/2c4ebf87c00dd6c5251f.webp)

    ```java
    // 取消在AQS中排队的Node
    private void cancelAcquire(Node node) {
        // 如果当前节点为null，直接忽略。
        if (node == null)
            return;
        //1. 线程设置为null
        node.thread = null;
    
        //2. 往前跳过被取消的节点，找到一个有效节点
        Node pred = node.prev;
        while (pred.waitStatus > 0)
            node.prev = pred = pred.prev;
    
        //3. 拿到了上一个节点之前的next
        Node predNext = pred.next;
    
        //4. 当前节点状态设置为1，代表节点取消
        node.waitStatus = Node.CANCELLED;
    
        // 脱离AQS队列的操作
        // 当前Node是尾结点，将tail从当前节点替换为上一个节点
        if (node == tail && compareAndSetTail(node, pred)) {
            compareAndSetNext(pred, predNext, null);
        } else {
            // 到这，上面的操作CAS操作失败
            int ws = pred.waitStatus;
            // 不是head的后继节点
            if (pred != head &&
                // 拿到上一个节点的状态，只要上一个节点的状态不是取消状态，就改为-1
                (ws == Node.SIGNAL || (ws <= 0 && compareAndSetWaitStatus(pred, ws, Node.SIGNAL))) 
                && pred.thread != null) {
                // 上面的判断都是为了避免后面节点无法被唤醒。
                // 前继节点是有效节点，可以唤醒后面的节点
                Node next = node.next;
                if (next != null && next.waitStatus <= 0)
                    compareAndSetNext(pred, predNext, next);
            } else {
                // 当前节点是head的后继节点
                unparkSuccessor(node);
            }
    
            node.next = node; // help GC
        }
    }
    ```

##### 3.3.2.3 lockInterruptibly方法

```java
// 这个是lockInterruptibly和tryLock(time,unit)唯一的区别
// lockInterruptibly，拿不到锁资源，就死等，等到锁资源释放后，被唤醒，或者是被中断唤醒
private void doAcquireInterruptibly(int arg) throws InterruptedException {
    final Node node = addWaiter(Node.EXCLUSIVE);
    boolean failed = true;
    try {
        for (;;) {
            final Node p = node.predecessor();
            if (p == head && tryAcquire(arg)) {
                setHead(node);
                p.next = null; // help GC
                failed = false;
                return;
            }
            if (shouldParkAfterFailedAcquire(p, node) && parkAndCheckInterrupt())
                // 中断唤醒抛异常！
                throw new InterruptedException();
        }
    } finally {
        if (failed)
            cancelAcquire(node);
    }
}

private final boolean parkAndCheckInterrupt() {
    LockSupport.park(this);
    // 这个方法可以确认，当前挂起的线程，是被中断唤醒的，还是被正常唤醒的。
    // 中断唤醒，返回true，如果是正常唤醒，返回false
    return Thread.interrupted();
}
```

### 3.4 释放锁流程源码剖析

#### 3.4.1 释放锁流程概述

![image.png](/blogs/_archive-2024-assets/de4f7acb0b7484d0ef25.webp)

#### 3.4.2 释放锁源码分析

```java
public void unlock() {
    // 释放锁资源不分为公平锁和非公平锁，都是一个sync对象
    sync.release(1);
}

// 释放锁的核心流程
public final boolean release(int arg) {
    // 核心释放锁资源的操作之一
    if (tryRelease(arg)) {
        // 如果锁已经释放掉了，走这个逻辑
        Node h = head;
        // h不为null，说明有排队的（录课时估计脑袋蒙圈圈。）
        // 如果h的状态不为0（为-1），说明后面有排队的Node，并且线程已经挂起了。
        if (h != null && h.waitStatus != 0)
            // 唤醒排队的线程
            unparkSuccessor(h);
        return true;
    }
    return false;
}
// ReentrantLock释放锁资源操作
protected final boolean tryRelease(int releases) {
    // 拿到state - 1（并没有赋值给state）
    int c = getState() - releases;
    // 判断当前持有锁的线程是否是当前线程，如果不是，直接抛出异常
    if (Thread.currentThread() != getExclusiveOwnerThread())
        throw new IllegalMonitorStateException();
    // free，代表当前锁资源是否释放干净了。
    boolean free = false;
    if (c == 0) {
        // 如果state - 1后的值为0，代表释放干净了。
        free = true;
        // 将持有锁的线程置位null
        setExclusiveOwnerThread(null);
    }
    // 将c设置给state
    setState(c);
    // 锁资源释放干净返回true，否则返回false
    return free;
}

// 唤醒后面排队的Node
private void unparkSuccessor(Node node) {
    // 拿到头节点状态
    int ws = node.waitStatus;
    if (ws < 0)
        // 先基于CAS，将节点状态从-1，改为0
        compareAndSetWaitStatus(node, ws, 0);
    // 拿到头节点的后续节点。
    Node s = node.next;
    // 如果后续节点为null或者，后续节点的状态为1，代表节点取消了。
    if (s == null || s.waitStatus > 0) {
        s = null;
        // 如果后续节点为null，或者后续节点状态为取消状态，从后往前找到一个有效节点环境
        for (Node t = tail; t != null && t != node; t = t.prev)
            // 从后往前找到状态小于等于0的节点
            // 找到离head最新的有效节点，并赋值给s
            if (t.waitStatus <= 0)
                s = t;
    }
    // 只要找到了这个需要被唤醒的节点，执行unpark唤醒
    if (s != null)
        LockSupport.unpark(s.thread);
}
```

### 3.5 AQS中常见的问题

#### 3.5.1 AQS中为什么要有一个虚拟的head节点

**AQS可以没有head，设计之初指定head只是为了更方便的操作。方便管理双向链表而已，一个哨兵节点的存在。**

比如ReentrantLock中释放锁资源时，会考虑是否需要唤醒后继节点。如果头结点的状态不是-1。就不需要去唤醒后继节点。唤醒后继节点时，需要找到head.next节点，如果head.next为null，或者是取消了，此时需要遍历整个双向链表，从后往前遍历，找到离head最近的Node。规避了一些不必要的唤醒操作。

如果不用虚拟节点（哨兵节点），当前节点挂起，当前节点的状态设置为-1。可行。AQS本身就是使用了哨兵节点做双向链表的一些操作。

网上说了，虚拟的head，可以避免重复唤醒操作。虚拟的head并没有处理这个问题。

#### 3.5.2 AQS中为什么使用双向链表

**AQS的双向链表就为了更方便的操作Node节点。**

在执行tryLock，lockInterruptibly方法时，如果在线程阻塞时，中断了线程，此时线程会执行cancelAcquire取消当前节点，不在AQS的双向链表中排队。如果是单向链表，此时会导致取消节点，无法直接将当前节点的prev节点的next指针，指向当前节点的next节点。

### 3.6 ConditionObject

#### 3.6.1 ConditionObject的介绍&应用

像synchronized提供了wait和notify的方法实现线程在持有锁时，可以实现挂起，已经唤醒的操作。

ReentrantLock也拥有这个功能。

ReentrantLock提供了await和signal方法去实现类似wait和notify的功能。

想执行await或者是signal就必须先持有lock锁的资源。

先look一下Condition的应用

```java
public static void main(String[] args) throws InterruptedException, IOException {
    ReentrantLock lock = new ReentrantLock();
    Condition condition = lock.newCondition();

    new Thread(() -> {
        lock.lock();
        System.out.println("子线程获取锁资源并await挂起线程");
        try {
            Thread.sleep(5000);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        try {
            condition.await();
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        System.out.println("子线程挂起后被唤醒！持有锁资源");

    }).start();
    Thread.sleep(100);
    // =================main======================
    lock.lock();
    System.out.println("主线程等待5s拿到锁资源，子线程执行了await方法");
    condition.signal();
    System.out.println("主线程唤醒了await挂起的子线程");
    lock.unlock();
}
```

#### 3.6.2 Condition的构建方式&核心属性

发现在通过lock锁对象执行newCondition方法时，本质就是直接new的AQS提供的ConditionObject对象

```java
final ConditionObject newCondition() {
    return new ConditionObject();
}
```

其实lock锁中可以有多个Condition对象。

在对Condition1进行操作时，不会影响到Condition2的单向链表。

其次可以发现ConditionObject中，只有两个核心属性：

```java
/** First node of condition queue. */
private transient Node firstWaiter;
/** Last node of condition queue. */
private transient Node lastWaiter;
```

虽然Node对象有prev和next，但是在ConditionObject中是不会使用这两个属性的，只要在Condition队列中，这两个属性都是null。在ConditionObject中只会使用nextWaiter的属性实现单向链表的效果。

#### 3.6.3 Condition的await方法分析（前置分析）

持有锁的线程在执行await方法后会做几个操作：

* 判断线程是否中断，如果中断了，什么都不做。
* 没有中断，就讲当前线程封装为Node添加到Condition的单向链表中
* 一次性释放掉锁资源。
* 如果当前线程没有在AQS队列，就正常执行LockSupport.park(this)挂起线程。

```java
、// await方法的前置分析，只分析到线程挂起
public final void await() throws InterruptedException {
    // 先判断线程的中断标记位是否是true
    if (Thread.interrupted())
        // 如果是true，就没必要执行后续操作挂起了。
        throw new InterruptedException();
    // 在线程挂起之前，先将当前线程封装为Node，并且添加到Condition队列中
    Node node = addConditionWaiter();
    // fullyRelease在释放锁资源，一次性将锁资源全部释放，并且保留重入的次数
    int savedState = fullyRelease(node);
    // 省略一行代码……
    // 当前Node是否在AQS队列中？
    // 执行fullyRelease方法后，线程就释放锁资源了，如果线程刚刚释放锁资源，其他线程就立即执行了signal方法，
    // 此时当前线程就被放到了AQS的队列中，这样一来线程就不需要执行LockSupport.park(this);去挂起线程了
    while (!isOnSyncQueue(node)) {
        // 如果没有在AQS队列中，正常在Condition单向链表里，正常挂起线程。
        LockSupport.park(this);
        // 省略部分代码……
    }
    // 省略部分代码……
}

// 线程挂起先，添加到Condition单向链表的业务~~
private Node addConditionWaiter() {
    // 拿到尾节点。
    Node t = lastWaiter;
    // 如果尾节点有值，并且尾节点的状态不正常，不是-2，尾节点可能要拜拜了~
    if (t != null && t.waitStatus != Node.CONDITION) {
        // 如果尾节点已经取消了，需要干掉取消的尾节点~
        unlinkCancelledWaiters();
        // 重新获取lastWaiter
        t = lastWaiter;
    }
    // 构建当前线程的Node，并且状态设置为-2
    Node node = new Node(Thread.currentThread(), Node.CONDITION);
    // 如果last节点为null。直接将当前节点设置为firstWaiter
    if (t == null)
        firstWaiter = node;
    else
        // 如果last节点不为null，说明有值，就排在lastWaiter的后面
        t.nextWaiter = node;
    // 把当前节点设置为最后一个节点
    lastWaiter = node;
    // 返回当前节点
    return node;
}

// 干掉取消的尾节点。
private void unlinkCancelledWaiters() {
    // 拿到头节点
    Node t = firstWaiter;
    // 声明一个节点，爱啥啥~~~
    Node trail = null;
    // 如果t不为null，就正常执行~~
    while (t != null) {
        // 拿到t的next节点
        Node next = t.nextWaiter;
        // 如果t的状态不为-2，说明有问题
        if (t.waitStatus != Node.CONDITION) {
            // t节点的next为null
            t.nextWaiter = null;
            // 如果trail为null，代表头结点状态就是1，
            if (trail == null)
                // 将头结点指向next节点
                firstWaiter = next;
            else
                // 如果trail有值，说明不是头结点位置
                trail.nextWaiter = next;
            // 如果next为null，说明单向链表遍历到最后了，直接结束
            if (next == null)
                lastWaiter = trail;
        }
        // 如果t的状态是-2，一切正常
        else {
            // 临时存储t
            trail = t;
        }
        // t指向之前的next
        t = next;
    }
}

// 一次性释放锁资源
final int fullyRelease(Node node) {
    // 标记位，释放锁资源默认失败！
    boolean failed = true;
    try {
        // 拿到现在state的值
        int savedState = getState();
        // 一次性释放干净全部锁资源
        if (release(savedState)) {
            // 释放锁资源失败了么？ 没有！
            failed = false;
            // 返回对应的锁资源信息
            return savedState;
        } else {
            throw new IllegalMonitorStateException();
        }
    } finally {
        if (failed)
            // 如果释放锁资源失败，将节点状态设置为取消
            node.waitStatus = Node.CANCELLED;
    }
}
```

#### 3.6.4 Condition的signal方法分析

分为了几个部分：

* 确保执行signal方法的是持有锁的线程
* 脱离Condition的队列
* 将Node状态从-2改为0
* 将Node添加到AQS队列
* 为了避免当前Node无法在AQS队列正常唤醒做了一些判断和操作

```java
// 线程挂起后，可以基于signal唤醒~
public final void signal() {
    // 在ReentrantLock中，如果执行signal的线程没有持有锁资源，直接扔异常
    if (!isHeldExclusively())
        throw new IllegalMonitorStateException();
    // 拿到排在Condition首位的Node
    Node first = firstWaiter;
    // 有Node在排队，才需要唤醒，如果没有，直接告辞~~
    if (first != null)
        doSignal(first);
}

// 开始唤醒Condition中的Node中的线程
private void doSignal(Node first) {
    // 先一波do-while走你~~~
    do {
        // 获取到第二个节点，并且将第二个节点设置为firstWaiter
        if ( (firstWaiter = first.nextWaiter) == null)
            // 说明就一个节点在Condition队列中，那么直接将firstWaiter和lastWaiter置位null
            lastWaiter = null;
        // 如果还有nextWaiter节点，因为当前节点要被唤醒了，脱离整个Condition队列。将nextWaiter置位null
        first.nextWaiter = null;
        // 如果transferForSignal返回true，一切正常，退出while循环
    } while (!transferForSignal(first) &&
            // 如果后续节点还有，往后面继续唤醒，如果没有，退出while循环
             (first = firstWaiter) != null);
}

// 准备开始唤醒在Condition中排队的Node
final boolean transferForSignal(Node node) {
    // 将在Condition队列中的Node的状态从-2，改为0，代表要扔到AQS队列了。
    if (!compareAndSetWaitStatus(node, Node.CONDITION, 0))
        // 如果失败了，说明在signal之前应当是线程被中断了，从而被唤醒了。
        return false;
    // 如果正常的将Node的状态从-2改为0，这是就要将Condition中的这个Node扔到AQS的队列。
    // 将当前Node扔到AQS队列，返回的p是当前Node的prev
    Node p = enq(node);
    // 获取上一个Node的状态
    int ws = p.waitStatus;
    // 如果ws > 0 ，说明这个Node已经被取消了。
    // 如果ws状态不是取消，将prev节点的状态改为-1,。
    if (ws > 0 || !compareAndSetWaitStatus(p, ws, Node.SIGNAL))
        // 如果prev节点已经取消了，可能会导致当前节点永远无法被唤醒。立即唤醒当前节点，基于acquireQueued方法，
            // 让当前节点找到一个正常的prev节点，并挂起线程
        // 如果prev节点正常，但是CAS修改prev节点失败了。证明prev节点因为并发原因导致状态改变。还是为了避免当前
            // 节点无法被正常唤醒，提前唤醒当前线程，基于acquireQueued方法，让当前节点找到一个正常的prev节点，并挂起线程
        LockSupport.unpark(node.thread);
    // 返回true
    return true;
}
```

#### 3.6.5 Conditiond的await方法分析（后置分析）

分为了几个部分：

* 唤醒之后，要先确认是中断唤醒还是signal唤醒，还是signal唤醒后被中断
* 确保当前线程的Node已经在AQS队列中
* 执行acquireQueued方法，等待锁资源。
* 在获取锁资源后，要确认是否在获取锁资源的阶段被中断过，如果被中断过，并且不是THROW_IE，那就确保interruptMode是REINTERRUPT。
* 确认当前Node已经不在Condition队列中了
* 最终根据interruptMode来决定具体做的事情
  * 0：嘛也不做。
  * THROW_IE：抛出异常
  * REINTERRUPT：执行线程的interrupt方法

```java
// 现在分析await方法的后半部分
public final void await() throws InterruptedException {
    if (Thread.interrupted())
        throw new InterruptedException();
    Node node = addConditionWaiter();
    int savedState = fullyRelease(node);
    // 中断模式~
    int interruptMode = 0;
    while (!isOnSyncQueue(node)) {
        LockSupport.park(this);
        // 如果线程执行到这，说明现在被唤醒了。
        // 线程可以被signal唤醒。（如果是signal唤醒，可以确认线程已经在AQS队列中）
        // 线程可以被interrupt唤醒，线程被唤醒后，没有在AQS队列中。
        // 如果线程先被signal唤醒，然后线程中断了。。。。（做一些额外处理）
        // checkInterruptWhileWaiting可以确认当前中如何唤醒的。
        // 返回的值，有三种
        // 0：正常signal唤醒，没别的事（不知道Node是否在AQS队列）
        // THROW_IE（-1）：中断唤醒，并且可以确保在AQS队列
        // REINTERRUPT（1）：signal唤醒，但是线程被中断了，并且可以确保在AQS队列
        if ((interruptMode = checkInterruptWhileWaiting(node)) != 0)
            break;
    }
    // Node一定在AQS队列
    // 执行acquireQueued，尝试在ReentrantLock中获取锁资源。
    // acquireQueued方法返回true：代表线程在AQS队列中挂起时，被中断过
    if (acquireQueued(node, savedState) && interruptMode != THROW_IE)
        // 如果线程在AQS队列排队时，被中断了，并且不是THROW_IE状态，确保线程的interruptMode是REINTERRUPT
        // REINTERRUPT：await不是中断唤醒，但是后续被中断过！！！
        interruptMode = REINTERRUPT;
    // 如果当前Node还在condition的单向链表中，脱离Condition的单向链表
    if (node.nextWaiter != null) 
        unlinkCancelledWaiters();
    // 如果interruptMode是0，说明线程在signal后以及持有锁的过程中，没被中断过，什么事都不做！
    if (interruptMode != 0)
        // 如果不是0~
        reportInterruptAfterWait(interruptMode);
}
// 判断当前线程被唤醒的模式，确认interruptMode的值。
private int checkInterruptWhileWaiting(Node node) {
    // 判断线程是否中断了。
    return Thread.interrupted() ?
        // THROW_IE：代表线程是被interrupt唤醒的，需要向上排除异常
        // REINTERRUPT：代表线程是signal唤醒的，但是在唤醒之后，被中断了。

        (transferAfterCancelledWait(node) ? THROW_IE : REINTERRUPT) :
        // 线程是正常的被signal唤醒，并且线程没有中断过。
        0;
}

// 判断线程到底是中断唤醒的，还是signal唤醒的！
final boolean transferAfterCancelledWait(Node node) {
    // 基于CAS将Node的状态从-2改为0
    if (compareAndSetWaitStatus(node, Node.CONDITION, 0)) {
        // 说明是中断唤醒的线程。因为CAS成功了。
        // 将Node添加到AQS队列中~（如果是中断唤醒的，当前线程同时存在Condition的单向链表以及AQS的队列中）
        enq(node);
        // 返回true
        return true;
    }
    // 判断当前的Node是否在AQS队列（signal唤醒的，但是可能线程还没放到AQS队列）
    // 等到signal方法将线程的Node扔到AQS队列后，再做后续操作
    while (!isOnSyncQueue(node))
        // 如果没在AQS队列上，那就线程让步，稍等一会，Node放到AQS队列再处理（看CPU）
        Thread.yield();
    // signal唤醒的，返回false
    return false;
}

// 确认Node是否在AQS队列上
final boolean isOnSyncQueue(Node node) {
    // 如果线程状态为-2，肯定没在AQS队列
    // 如果prev节点的值为null，肯定没在AQS队列
    if (node.waitStatus == Node.CONDITION || node.prev == null)
        // 返回false
        return false;
    // 如果节点的next不为null。说明已经在AQS队列上。、
    if (node.next != null) 
        // 确定AQS队列上有！
        return true;
    // 如果上述判断都没有确认节点在AQS队列上，在AQS队列中寻找一波
    return findNodeFromTail(node);
}
// 在AQS队列中找当前节点
private boolean findNodeFromTail(Node node) {
    // 拿到尾节点
    Node t = tail;
    for (;;) {
        // tail是否是当前节点，如果是，说明在AQS队列
        if (t == node)
            // 可以跳出while循环
            return true;
        // 如果节点为null，AQS队列中没有当前节点
        if (t == null)
            // 进入while，让步一手
            return false;
        // t向前引用
        t = t.prev;
    }
}

private void reportInterruptAfterWait(int interruptMode) throws InterruptedException {
    // 如果是中断唤醒的await，直接抛出异常！
    if (interruptMode == THROW_IE)
        throw new InterruptedException();
    // 如果是REINTERRUPT，signal后被中断过
    else if (interruptMode == REINTERRUPT)
        // 确认线程的中断标记位是true
        // Thread.currentThread().interrupt();
        selfInterrupt();
}
```

#### 3.6.6 Condition的awaitNanos&signalAll方法分析

awaitNanos：仅仅是在await方法的基础上，做了一内内的改变，整体的逻辑思想都是一样的。

挂起线程时，传入要阻塞的时间，时间到了，自动唤醒，走添加到AQS队列的逻辑

```java
// await指定时间，多了个时间到了自动醒。
public final long awaitNanos(long nanosTimeout)
        throws InterruptedException {
    if (Thread.interrupted())
        throw new InterruptedException();
    Node node = addConditionWaiter();
    int savedState = fullyRelease(node);
    // deadline：当前线程最多挂起到什么时间点
    final long deadline = System.nanoTime() + nanosTimeout;
    int interruptMode = 0;
    while (!isOnSyncQueue(node)) {
        // nanosTimeout的时间小于等于0，直接告辞！！
        if (nanosTimeout <= 0L) {
            // 正常扔到AQS队列
            transferAfterCancelledWait(node);
            break;
        }
        // nanosTimeout的时间大于1000纳秒时，才可以挂起线程
        if (nanosTimeout >= spinForTimeoutThreshold)
            // 如果大于，正常挂起
            LockSupport.parkNanos(this, nanosTimeout);
        if ((interruptMode = checkInterruptWhileWaiting(node)) != 0)
            break;
        // 计算剩余的挂起时间，可能需要重新的走while循环，再次挂起线程
        nanosTimeout = deadline - System.nanoTime();
    }
    if (acquireQueued(node, savedState) && interruptMode != THROW_IE)
        interruptMode = REINTERRUPT;
    if (node.nextWaiter != null)
        unlinkCancelledWaiters();
    if (interruptMode != 0)
        reportInterruptAfterWait(interruptMode);
    // 剩余的挂起时间
    return deadline - System.nanoTime();
}
```

signalAll方法。这个方法一看就懂，之前signal是唤醒1个，这个是全部唤醒

```java
// 以do-while的形式，将Condition单向链表中的所有Node，全部唤醒并扔到AQS队列
private void doSignalAll(Node first) {
    // 将头尾都置位null~
    lastWaiter = firstWaiter = null;
    do {
        // 拿到next节点的引用
        Node next = first.nextWaiter;
        // 断开当前Node的nextWaiter
        first.nextWaiter = null;
        // 修改Node状态，扔AQS队列，是否唤醒！
        transferForSignal(first);
        // 指向下一个节点
        first = next;
    } while (first != null);
}
```

## 四、**深入ReentrantReadWriteLock**

### 一、为什么要出现读写锁

synchronized和ReentrantLock都是互斥锁。

如果说有一个操作是读多写少的，还要保证线程安全的话。如果采用上述的两种互斥锁，效率方面很定是很低的。

在这种情况下，咱们就可以使用ReentrantReadWriteLock读写锁去实现。

读读之间是不互斥的，可以读和读操作并发执行。

但是如果涉及到了写操作，那么还得是互斥的操作。

```java
static ReentrantReadWriteLock lock = new ReentrantReadWriteLock();

static ReentrantReadWriteLock.WriteLock writeLock = lock.writeLock();

static ReentrantReadWriteLock.ReadLock readLock = lock.readLock();

public static void main(String[] args) throws InterruptedException {
    new Thread(() -> {
        readLock.lock();
        try {
            System.out.println("子线程！");
            try {
                Thread.sleep(500000);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        } finally {
            readLock.unlock();
        }
    }).start();

    Thread.sleep(1000);
    writeLock.lock();
    try {
        System.out.println("主线程！");
    } finally {
        writeLock.unlock();
    }
}
```

### 二、读写锁的实现原理

**ReentrantReadWriteLock还是基于AQS实现的，还是对state进行操作，拿到锁资源就去干活，如果没有拿到，依然去AQS队列中排队。**

**读锁操作：基于state的高16位进行操作。**

**写锁操作：基于state的低16为进行操作。**

**ReentrantReadWriteLock依然是可重入锁。**

**写锁重入**：读写锁中的写锁的重入方式，基本和ReentrantLock一致，没有什么区别，依然是对state进行+1操作即可，只要确认持有锁资源的线程，是当前写锁线程即可。只不过之前ReentrantLock的重入次数是state的正数取值范围，但是读写锁中写锁范围就变小了。

**读锁重入**：因为读锁是共享锁。读锁在获取锁资源操作时，是要对state的高16位进行 + 1操作。因为读锁是共享锁，所以同一时间会有多个读线程持有读锁资源。这样一来，多个读操作在持有读锁时，无法确认每个线程读锁重入的次数。为了去记录读锁重入的次数，每个读操作的线程，都会有一个ThreadLocal记录锁重入的次数。

**写锁的饥饿问题**：读锁是共享锁，当有线程持有读锁资源时，再来一个线程想要获取读锁，直接对state修改即可。在读锁资源先被占用后，来了一个写锁资源，此时，大量的需要获取读锁的线程来请求锁资源，如果可以绕过写锁，直接拿资源，会造成写锁长时间无法获取到写锁资源。

**读锁在拿到锁资源后，如果再有读线程需要获取读锁资源，需要去AQS队列排队。如果队列的前面需要写锁资源的线程，那么后续读线程是无法拿到锁资源的。持有读锁的线程，只会让写锁线程之前的读线程拿到锁资源**

### 三、写锁分析

#### 3.1 写锁加锁流程概述

![image.png](/blogs/_archive-2024-assets/31865575b5e69989073c.webp)

#### 3.2 写锁加锁源码分析

写锁加锁流程

```java
// 写锁加锁的入口
public void lock() {
    sync.acquire(1);
}

// 阿巴阿巴！！
public final void acquire(int arg) {
    if (!tryAcquire(arg) &&
        acquireQueued(addWaiter(Node.EXCLUSIVE), arg))
        selfInterrupt();
}

// 读写锁的写锁实现tryAcquire
protected final boolean tryAcquire(int acquires) {
    // 拿到当前线程
    Thread current = Thread.currentThread();
    // 拿到state的值
    int c = getState();
    // 得到state低16位的值
    int w = exclusiveCount(c);
    // 判断是否有线程持有着锁资源
    if (c != 0) {
        // 当前没有线程持有写锁，读写互斥，告辞。
        // 有线程持有写锁，持有写锁的线程不是当前线程，不是锁重入，告辞。
        if (w == 0 || current != getExclusiveOwnerThread())
            return false;
        // 当前线程持有写锁。 锁重入。
        if (w + exclusiveCount(acquires) > MAX_COUNT)
            throw new Error("Maximum lock count exceeded");
        // 没有超过锁重入的次数，正常 + 1
        setState(c + acquires);
        return true;
    }
    // 尝试获取锁资源
    if (writerShouldBlock() ||
        // CAS拿锁
        !compareAndSetState(c, c + acquires))
        return false;
    // 拿锁成功，设置占有互斥锁的线程
    setExclusiveOwnerThread(current);
    // 返回true
    return true;
}

// ================================================================
// 这个方法是将state的低16位的值拿到
int w = exclusiveCount(c);
state & ((1 << 16) - 1)
00000000 00000000 00000000 00000001    ==   1
00000000 00000001 00000000 00000000    ==   1 << 16
00000000 00000000 11111111 11111111    ==   (1 << 16) - 1
&运算，一个为0，必然为0，都为1，才为1
// ================================================================
// writerShouldBlock方法查看公平锁和非公平锁的效果
// 非公平锁直接返回false执行CAS尝试获取锁资源
// 公平锁需要查看是否有排队的，如果有排队的，我是否是head的next
```

#### 3.3 写锁释放锁流程概述&释放锁源码

释放的流程和ReentrantLock一致，只是在判断释放是否干净时，判断低16位的值

```java
// 写锁释放锁的tryRelease方法
protected final boolean tryRelease(int releases) {
    // 判断当前持有写锁的线程是否是当前线程
    if (!isHeldExclusively())
        throw new IllegalMonitorStateException();
    // 获取state - 1
    int nextc = getState() - releases;
    // 判断低16位结果是否为0，如果为0，free设置为true
    boolean free = exclusiveCount(nextc) == 0;
    if (free)
        // 将持有锁的线程设置为null
        setExclusiveOwnerThread(null);
    // 设置给state
    setState(nextc);
    // 释放干净，返回true。  写锁有冲入，这里需要返回false，不去释放排队的Node
    return free;
}
```

### 四、读锁分析

#### 4.1 读锁加锁流程概述

1、分析读锁加速的基本流程

2、分析读锁的可重入锁实现以及优化

3、解决ThreadLocal内存泄漏问题

4、读锁获取锁自后，如果唤醒AQS中排队的读线程

#### 4.1.1 基础读锁流程

![image.png](/blogs/_archive-2024-assets/ad65df3d955abe6a8520.webp)

针对上述简单逻辑的源码分析

```java
// 读锁加锁的方法入口
public final void acquireShared(int arg) {
    // 竞争锁资源滴干活
    if (tryAcquireShared(arg) < 0)
        // 没拿到锁资源，去排队
        doAcquireShared(arg);
}

// 读锁竞争锁资源的操作
protected final int tryAcquireShared(int unused) {
    // 拿到当前线程
    Thread current = Thread.currentThread();
    // 拿到state
    int c = getState();
    // 拿到state的低16位，判断 != 0，有写锁占用着锁资源
    // 并且，当前占用锁资源的线程不是当前线程
    if (exclusiveCount(c) != 0 && getExclusiveOwnerThread() != current)
        // 写锁被其他线程占用，无法获取读锁，直接返回 -1，去排队
        return -1;
    // 没有线程持有写锁、当前线程持有写锁
    // 获取读锁的信息，state的高16位。
    int r = sharedCount(c);
    // 公平锁：就查看队列是由有排队的，有排队的，直接告辞，进不去if，后面也不用判断（没人排队继续走）
    // 非公平锁：没有排队的，直接抢。 有排队的，但是读锁其实不需要排队，如果出现这个情况，大部分是写锁资源刚刚释放，
    // 后续Node还没有来记得拿到读锁资源，当前竞争的读线程，可以直接获取
    if (!readerShouldBlock() &&
        // 判断持有读锁的临界值是否达到
        r < MAX_COUNT &&
        // CAS修改state，对高16位进行 + 1
        compareAndSetState(c, c + SHARED_UNIT)) {
        // 省略部分代码！！！！
        return 1;
    }
    return fullTryAcquireShared(current);
}
// 非公平锁的判断
final boolean apparentlyFirstQueuedIsExclusive() {
    Node h, s;
    return (h = head) != null &&    // head为null，可以直接抢占锁资源
        (s = h.next)  != null &&    // head的next为null，可以直接抢占锁资源
        !s.isShared()         &&    // 如果排在head后面的Node，是共享锁，可以直接抢占锁资源。
        s.thread != null;           // 后面排队的thread为null，可以直接抢占锁资源
}
```

#### 4.1.2 读锁重入流程

> =============================重入操作================
>
> 前面阐述过，读锁为了记录锁重入的次数，需要让每个读线程用ThreadLocal存储重入次数
>
> ReentrantReadWriteLock对读锁重入做了一些优化操作
>
> ============================记录重入次数的核心================
>
> ReentrantReadWriteLock在内部对ThreadLocal做了封装，基于HoldCount的对象存储重入次数，在内部有个count属性记录，而且每个线程都是自己的ThreadLocalHoldCounter，所以可以直接对内部的count进行++操作。
>
> =============================第一个获取读锁资源的重入次数记录方式================
>
> 第一个拿到读锁资源的线程，不需要通过ThreadLocal存储，内部提供了两个属性来记录第一个拿到读锁资源线程的信息
>
> 内部提供了firstReader记录第一个拿到读锁资源的线程，firstReaderHoldCount记录firstReader的锁重入次数
>
> ==============================最后一个获取读锁资源的重入次数记录方式================
>
> 最后一个拿到读锁资源的线程，也会缓存他的重入次数，这样++起来更方便
>
> 基于cachedHoldCounter缓存最后一个拿到锁资源现成的重入次数
>
> ==============================最后一个获取读锁资源的重入次数记录方式================
>
> 重入次数的流程执行方式：
>
> 1、判断当前线程是否是第一个拿到读锁资源的：如果是，直接将firstReader以及firstReaderHoldCount设置为当前线程的信息
>
> 2、判断当前线程是否是firstReader：如果是，直接对firstReaderHoldCount++即可。
>
> 3、跟firstReader没关系了，先获取cachedHoldCounter，判断是否是当前线程。
>
> 3.1、如果不是，获取当前线程的重入次数，将cachedHoldCounter设置为当前线程。
>
> 3.2、如果是，判断当前重入次数是否为0，重新设置当前线程的锁从入信息到readHolds（ThreadLocal）中，算是初始化操作，重入次数是0
>
> 3.3、前面两者最后都做count++

上述逻辑源码分析

```java
protected final int tryAcquireShared(int unused) {
    Thread current = Thread.currentThread();
    int c = getState();
    if (exclusiveCount(c) != 0 &&
        getExclusiveOwnerThread() != current)
        return -1;
    int r = sharedCount(c);
    if (!readerShouldBlock() &&
        r < MAX_COUNT &&
        compareAndSetState(c, c + SHARED_UNIT)) {
        // ===============================================================
        // 判断r == 0，当前是第一个拿到读锁资源的线程
        if (r == 0) {
            // 将firstReader设置为当前线程
            firstReader = current;
            // 将count设置为1
            firstReaderHoldCount = 1;
        } 
        // 判断当前线程是否是第一个获取读锁资源的线程
        else if (firstReader == current) {
            // 直接++。
            firstReaderHoldCount++;
        } 
        // 到这，就说明不是第一个获取读锁资源的线程
        else {
            // 那获取最后一个拿到读锁资源的线程
            HoldCounter rh = cachedHoldCounter;
            // 判断当前线程是否是最后一个拿到读锁资源的线程
            if (rh == null || rh.tid != getThreadId(current))
                // 如果不是，设置当前线程为cachedHoldCounter
                cachedHoldCounter = rh = readHolds.get();
            // 当前线程是之前的cacheHoldCounter
            else if (rh.count == 0)
                // 将当前的重入信息设置到ThreadLocal中
                readHolds.set(rh);
            // 重入的++
            rh.count++;
        }
        // ===============================================================
        return 1;
    }
    return fullTryAcquireShared(current);
}
```

#### 4.1.3 读锁加锁的后续逻辑fullTryAcquireShared

```java
// tryAcquireShard方法中，如果没有拿到锁资源，走这个方法，尝试再次获取，逻辑跟上面基本一致。
final int fullTryAcquireShared(Thread current) {
    // 声明当前线程的锁重入次数
    HoldCounter rh = null;
    // 死循环
    for (;;) {
        // 再次拿到state
        int c = getState();
        // 当前如果有写锁在占用锁资源，并且不是当前线程，返回-1，走排队策略
        if (exclusiveCount(c) != 0) {
            if (getExclusiveOwnerThread() != current)
                return -1;

        } 
        // 查看当前是否可以尝试竞争锁资源（公平锁和非公平锁的逻辑）
        else if (readerShouldBlock()) {
            // 无论公平还是非公平，只要进来，就代表要放到AQS队列中了，先做一波准备
            // 在处理ThreadLocal的内存泄漏问题
            if (firstReader == current) {
                // 如果当前当前线程是之前的firstReader，什么都不用做
            } else {
                // 第一次进来是null。
                if (rh == null) {
                    // 拿到最后一个获取读锁的线程
                    rh = cachedHoldCounter;
                    // 当前线程并不是cachedHoldCounter，没到拿到
                    if (rh == null || rh.tid != getThreadId(current)) {
                        // 从自己的ThreadLocal中拿到重入计数器
                        rh = readHolds.get();
                        // 如果计数器为0，说明之前没拿到过读锁资源
                        if (rh.count == 0)
                            // remove，避免内存泄漏
                            readHolds.remove();
                    }
                }
                // 前面处理完之后，直接返回-1
                if (rh.count == 0)
                    return -1;
            }
        }
        // 判断重入次数，是否超出阈值
        if (sharedCount(c) == MAX_COUNT)
            throw new Error("Maximum lock count exceeded");
        // CAS尝试获取锁资源
        if (compareAndSetState(c, c + SHARED_UNIT)) {
            if (sharedCount(c) == 0) {
                firstReader = current;
                firstReaderHoldCount = 1;
            } else if (firstReader == current) {
                firstReaderHoldCount++;
            } else {
                if (rh == null)
                    rh = cachedHoldCounter;
                if (rh == null || rh.tid != getThreadId(current))
                    rh = readHolds.get();
                else if (rh.count == 0)
                    readHolds.set(rh);
                rh.count++;
                cachedHoldCounter = rh; // cache for release
            }
            return 1;
        }
    }
}
```

#### 4.1.4 读线程在AQS队列获取锁资源的后续操作

> 1、正常如果都是读线程来获取读锁资源，不需要使用到AQS队列的，直接CAS操作即可
>
> 2、如果写线程持有着写锁，这是读线程就需要进入到AQS队列排队，可能会有多个读线程在AQS中。
>
> 当写锁释放资源后，会唤醒head后面的读线程，当head后面的读线程拿到锁资源后，还需要查看next节点是否也是读线程在阻塞，如果是，直接唤醒

源码分析

```java
// 读锁需要排队的操作
private void doAcquireShared(int arg) {
    // 声明Node，类型是共享锁，并且扔到AQS中排队
    final Node node = addWaiter(Node.SHARED);
    boolean failed = true;
    try {
        boolean interrupted = false;
        for (;;) {
            // 拿到上一个节点
            final Node p = node.predecessor();
            // 如果prev节点是head，直接可以执行tryAcquireShared
            if (p == head) {
                int r = tryAcquireShared(arg);
                if (r >= 0) {
                    // 拿到读锁资源后，需要做的后续处理
                    setHeadAndPropagate(node, r);
                    p.next = null; // help GC
                    if (interrupted)
                        selfInterrupt();
                    failed = false;
                    return;
                }
            }
            // 找到prev有效节点，将状态设置为-1，挂起当前线程
            if (shouldParkAfterFailedAcquire(p, node) &&
                parkAndCheckInterrupt())
                interrupted = true;
        }
    } finally {
        if (failed)
            cancelAcquire(node);
    }
}

private void setHeadAndPropagate(Node node, int propagate) {
    // 拿到head节点
    Node h = head; 
    // 将当前节点设置为head节点
    setHead(node);
    // 第一个判断更多的是在信号量有处理JDK1.5 BUG的操作。
    if (propagate > 0 || h == null || h.waitStatus < 0 || (h = head) == null || h.waitStatus < 0) {
        // 拿到当前Node的next节点
        Node s = node.next;
        // 如果next节点是共享锁，直接唤醒next节点
        if (s == null || s.isShared())
            doReleaseShared();
    }
}
```

### 4.2 读锁的释放锁流程

1、处理重入以及state的值

2、唤醒后续排队的Node

源码分析

```java
// 读锁释放锁流程
public final boolean releaseShared(int arg) {
    // tryReleaseShared：处理state的值，以及可重入的内容
    if (tryReleaseShared(arg)) {
        // AQS队列的事！
        doReleaseShared();
        return true;
    }
    return false;
}

// 1、 处理重入问题  2、 处理state
protected final boolean tryReleaseShared(int unused) {
    // 拿到当前线程
    Thread current = Thread.currentThread();
    // 如果是firstReader，直接干活，不需要ThreadLocal
    if (firstReader == current) {
        // assert firstReaderHoldCount > 0;
        if (firstReaderHoldCount == 1)
            firstReader = null;
        else
            firstReaderHoldCount--;
    } 
    // 不是firstReader，从cachedHoldCounter以及ThreadLocal处理
    else {
        // 如果是cachedHoldCounter，正常--
        HoldCounter rh = cachedHoldCounter;
        // 如果不是cachedHoldCounter，从自己的ThreadLocal中拿
        if (rh == null || rh.tid != getThreadId(current))
            rh = readHolds.get();
        int count = rh.count;
        // 如果为1或者更小，当前线程就释放干净了，直接remove，避免value内存泄漏
        if (count <= 1) {
            readHolds.remove();
            // 如果已经是0，没必要再unlock，扔个异常
            if (count <= 0)
                throw unmatchedUnlockException();
        }
        // -- 走你。
        --rh.count;
    }
    for (;;) {
        // 拿到state，高16位，-1，成功后，返回state是否为0
        int c = getState();
        int nextc = c - SHARED_UNIT;
        if (compareAndSetState(c, nextc))
            return nextc == 0;
    }
}

// 唤醒AQS中排队的线程
private void doReleaseShared() {
    // 死循环
    for (;;) {
        // 拿到头
        Node h = head;
        // 说明有排队的
        if (h != null && h != tail) {
            // 拿到head的状态
            int ws = h.waitStatus;
            // 判断是否为 -1 
            if (ws == Node.SIGNAL) {
                // 到这，说明后面有挂起的线程，先基于CAS将head的状态从-1，改为0
                if (!compareAndSetWaitStatus(h, Node.SIGNAL, 0))
                    continue;   
                // 唤醒后续节点
                unparkSuccessor(h);
            }
            // 这里不是给读写锁准备的，在信号量里说。。。
            else if (ws == 0 && !compareAndSetWaitStatus(h, 0, Node.PROPAGATE))
                continue;
        }
        // 这里是出口
        if (h == head)   
            break;
    }
}
```

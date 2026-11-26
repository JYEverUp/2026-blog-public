## 一、VueX

1. 概念
   ​ 在Vue中实现集中式状态（数据）管理的一个Vue插件，对vue应用中多个组件的共享状态进行集中式的管理（读/写），也是一种组件间通信的方式，且适用于任意组件间通信。
2. 何时使用？
   ​ 多个组件需要共享数据时
3. 原理
   ![Vuex原理图](/blogs/_archive-2024-assets/27f9c3114cc366537ff3.webp)

### 1. 搭建vuex 环境

1. 创建文件：src/store/index.js

```js
// 创建store

import Vue from "vue";
// 引入vuex
import Vuex,{ Store } from "vuex"
// 使用插件
Vue.use(Vuex)

// 准备actions对象——响应组件中用户的动作
const actions = {}
// mutations -- 处理组件操作
const mutations = {}
// state -- 存储数据
const state = {}

// 暴露store
export default new Store({
  actions,
  mutations,
  state
})
```

2. 在main.js中创建vm时传入store配置项

```js
......
//引入store
import store from './store'
......

//创建vm
new Vue({
	el:'#app',
	render: h => h(App),
	store
})
```

#### 2. vuex基本使用

初始化数据、配置actions、配置mutations，操作文件store.js

```js
import Vue from "vue";
// 引入vuex
import Vuex,{ Store } from "vuex"
// 使用插件
Vue.use(Vuex)

// actions -- 响应组件操作状态
const actions = {
  incrementAsync:function(conText,value) {
    setTimeout(()=>{
      conText.commit('INCREMENTASYNC',value)
    },1000)
  },
  incrementOdd:function(conText,value) {
    if (conText.state.sum % 2) {
      conText.commit('INCREMENTASYNC',value)
    }
  }
}
// mutations -- 处理组件操作
const mutations = {
  INCREMENT:function(state,value) {
    state.sum += value
  },
  DECREMENT:function(state,value) {
    state.sum -= value
  },
  INCREMENTODD:function(state,value) {
    state.sum += value
  },
  INCREMENTASYNC:function(state,value) {
    state.sum += value
  }
}
// state -- 存储数据
const state = {
  sum:0
}
// 暴露store
export default new Store({
  actions,
  mutations,
  state
})
```

- 组件中读取vuex中的数据：`$store.state.sum`
- 组件中修改vuex中的数据：`$store.dispatch('action中的方法名',数据)`或`$store.commit`('mutations中的方法名',数据)
- 备注：若没有网络请求或其他业务逻辑，组件中也可以越过actions，即不写dispatch，直接编写commit

```html
<template>
  <div>
    <h3>当前求和结果为: {{$store.state.sum}}</h3>
    <div>
      <select name="" id="" v-model.number="inputNumber">
        <option value="1">1</option>
        <option value="2">2</option>
        <option value="3">3</option>
      </select>
      <button @click="increment">+</button>
      <button @click="decrement">-</button>
      <button @click="incrementOdd">结果为奇数再加</button>
      <button @click="incrementAsync">异步+</button>
    </div>
  </div>
</template>

<script>
export default {
  name:"Category",
  data() {
    return {
      inputNumber: 1
    }
  },
  methods: {
    increment() {
      this.$store.commit('INCREMENT',this.inputNumber)
    },
    decrement() {
      this.$store.commit('DECREMENT',this.inputNumber)
    },
    incrementOdd() {
      this.$store.dispatch('incrementOdd',this.inputNumber)
      
    },
    incrementAsync () {
      this.$store.dispatch('incrementAsync',this.inputNumber)
    }
  },
}
</script>
```

#### 3. getters

概念：当state中的数据需要经过加工后再使用时，可以使用getters加工。
在store.js中追加getters配置

```js
import Vue from "vue";
// 引入vuex
import Vuex,{ Store } from "vuex"
// 使用插件
Vue.use(Vuex)

// actions -- 响应组件操作状态
const actions = {
  ...
}
// mutations -- 处理组件操作
const mutations = {
  ...
}
// state -- 存储数据
const state = {
  sum:0
}
const getters = {
  bigSum(state) {
    return state.sum>0?state.sum*(state.sum-1):state.sum
  }
}
// 暴露store
export default new Store({
  ... ,
  getters
})
```

组件中读取数据：$store.getters.bigSum

```html
<template>
  <div>
    <h3>当前求和结果为: {{$store.state.sum}}</h3>
    <h3>放大十倍的结果为: {{$store.getters.bigSum}}</h3>
  </div>
</template>
```

#### 4. vuex 中的四个 map 方法

1. mapState 映射 state 中的数据为计算属性

```js
// store.js
const state = {
  school: 'xxx',
  sum: 0,
}

//组件计算属性
computed: {
  // 借助 mapState 生成计算属性：sum、school（对象写法）
   ...mapState({sum:'sum',school:'school'}),
  // 借助 mapState 生成计算属性：sum、school（数组写法）
  ...mapState(['sum','school']),
}
```

2. mapGetters 映射 getters 中的数据为计算属性

```js
// store.js
const getters = {
  bigSum(state) {
    return state.sum>0?state.sum*(state.sum-1):state.sum
  }
}

//组件计算属性
computed: {
  // 借助 mapGetters 生成计算属性：bigSum（对象写法）
  ...mapGetters({bigSum:'bigSum'}),
  // 借助 mapGetters 生成计算属性：bigSum（数组写法）
  ...mapGetters(['bigSum']),
}
```

3. mapActions与mapMutations
   帮助我们生成与actions对话的方法，即：包含`$store.dispatch(xxx)`的函数

```js
methods: {
  // increment() {
  //   this.$store.commit('INCREMENT',this.inputNumber)
  // },
  // decrement() {
  //   this.$store.commit('DECREMENT',this.inputNumber)
  // },
  //语法糖：靠 mapActions生成：increment、decrement（对象形式）
  ...mapMutations({increment:'increment',decrement:'decrement'}),
  ...mapMutations(['increment','decrement']),

  // incrementOdd() {
  //   this.$store.dispatch('incrementOdd',this.inputNumber)
    
  // },
  // incrementAsync () {
  //   this.$store.dispatch('incrementAsync',this.inputNumber)
  // }
  //语法糖：靠 mapActions 生成：incrementOdd、incrementAsync两种方式
  ...mapActions({incrementOdd:'incrementOdd',incrementAsync:'incrementAsync'})
  ...mapActions(['incrementOdd','incrementAsync'])
}
```

#### 5. vuex 模块化

目的：让代码更好维护，让多种数据分类更加明确。
store.js

```js
// countAbout personAbout 可以封装为文件并单独引入
const countAbout = {
  namespaced:true,//开启命名空间
  state:{x:1},
  mutations: { ... },
  actions: { ... },
  getters: {
    bigSum(state){
       return state.sum * 10
    }
  }
}

const personAbout = {
  namespaced:true,//开启命名空间
  state:{ ... },
  mutations: { ... },
  actions: { ... }
}

const store = new Vuex.Store({
  modules: {
    countAbout,
    personAbout
  }
})
```

读取 state 数据

```js
//方式一：自己直接读取
this.$store.state.personAbout.list
//方式二：借助 mapState 读取：用 mapState 取 countAbout 中的state 必须加上 'countAbout'
computed:{
  ...mapState('countAbout',['sum','school','subject']),
}
```

读取 getters 数据

```js
//方式一：自己直接读取
this.$store.getters['personAbout/firstPersonName']
//方式二：借助 mapGetters 读取：
...mapGetters('countAbout',['bigSum'])
```

组件中调用 commit 

```js
//方式一：自己直接 commit
this.$store.commit('personAbout/ADD_PERSON',person)
//方式二：借助 mapMutations：
...mapMutations('countAbout',{increment:'INCREMENT',decrement:'DECREMENT'}),
```

组件中调用 dispath 

```js
//方式一：自己直接 dispath
this.$store.dispatch('persionAbout/addForServe',{})
//方式二：借助 mapMutations：
...mapActions('countAbout',['incrementOdd','incrementAsync']),
```

示例：

```js
// 创建store
import Vue from "vue";
// 引入vuex
import Vuex,{ Store } from "vuex"
import countOptains from './count'
import persionOptains from './persion'
// 使用插件
Vue.use(Vuex)

// 暴露store
export default new Store({
  modules: {
    countAbout:countOptains,
    persionAbout:persionOptains
  }
})

// count.js
export default {
  namespaced:true,
  actions:{
    incrementAsync:function(conText,value) {
      setTimeout(()=>{
        conText.commit('INCREMENTASYNC',value)
      },1000)
    },
    incrementOdd:function(conText,value) {
      if (conText.state.sum % 2) {
        conText.commit('INCREMENTASYNC',value)
      }
    }
  },
  mutations:{
    INCREMENT:function(state,value) {
      state.sum += value
    },
    DECREMENT:function(state,value) {
      state.sum -= value
    },
    INCREMENTODD:function(state,value) {
      state.sum += value
    },
    INCREMENTASYNC:function(state,value) {
      state.sum += value
    },
  },
  state:{
    sum:0,
    name:'lisi',
  },
  getters:{
    bigSum(state) {
      return state.sum>0?state.sum*(state.sum-1):state.sum
    }
  }
}

// persion.js
import axios from "axios";
export default {
  namespaced:true,
  actions:{
    addWang:function(conText,value) {
      if (value.name.startsWith('王')) {
        conText.commit('ADD_PERSION',value)
      }else {
        alert('包含王吗？')
      }
    },
    addForServe:function(conText,value) {
      axios.get('https://api.uixsj.cn/hitokoto/get').then(
        (response)=>{
          console.log(response.data);
          conText.commit('ADD_SERVE',response.data)
        },
        (error)=>{
          console.log(error)
        }
      )
      // conText.commit('ADD_PERSION',value)
    }
  },
  mutations:{
    ADD_PERSION:function(state,value) {
      state.persionList.unshift(value)
    },
    ADD_SERVE:function (state,value) {
      state.serverStr = value
    }
  },
  state:{
    persionList:[
      {id:'001',name:'admin'},
      {id:'002',name:'张三'}
    ],
    serverStr:''
  },
  getters:{
    firstName(state) {
      return state.persionList[0].name
    }
  }
}
```

```js
// main.js
import Vue from 'vue'
import App from "./App.vue";

// 引入store
import store from "./store";

const vm = new Vue({
  el:'#app',
  store,
  render:n=>n(App),
  beforeCreate() {
    Vue.prototype.$bus = this //全局事件总线
  }
})

```

```js
// Counter.vue
<template>
  <div>
    <h3>Persion 组件</h3>
    <h4>当前组件求和结果为: {{sum}}</h4>
    <h4>n*(n-1)的结果为: {{bigSum}}</h4>
    <h4>下方组件的总人数为：{{persions.length}}</h4>
    <div>
      <select name="" id="" v-model.number="inputNumber">
        <option value="1">1</option>
        <option value="2">2</option>
      </select>
      <button @click="increment(inputNumber)">+</button>
      <button @click="decrement(inputNumber)">-</button>
      <button @click="incrementOdd(inputNumber)">结果为奇数再加</button>
      <button @click="incrementAsync(inputNumber)">异步+</button>
    </div>
  </div>
</template>

<script>
import { mapState,mapGetters,mapMutations,mapActions } from "vuex";
export default {
  name:"Category",
  data() {
    return {
      inputNumber: 1
    }
  },
  methods: {
    ...mapMutations('countAbout',{increment:'INCREMENT',decrement:'DECREMENT'}),
    ...mapActions('countAbout',['incrementOdd','incrementAsync']),

  },
  computed:{
    ...mapState('countAbout',{sum:'sum',name:'name'}),
    ...mapState('persionAbout',{persions:'persionList'}),
    ...mapGetters('countAbout',{bigSum:'bigSum'}),
  }
}
</script>

<style>
  button {
    margin: 0 5px;
  }
</style>
```

```js
// Peersion.vue
<template>
  <div>
    <h3>Persion 组件 </h3>
    <span v-show="serveStr">{{serveStr}}</span>
    <h4>上方组件求和为 {{sum}}</h4>
    <h4>首个人名 {{firstName}}</h4>
    <input type="text" placeholder="输入姓名" v-model="inputName">
    <button @click="add">添加</button>
    <button @click="add_wang">添加名字含王的人</button>
    <ul>
      <li v-for="item in persions" :key="item.id">{{item.name}}</li>
    </ul>
  </div>
</template>

<script>
export default {
  name:'Persion',
  data() {
    return {
      inputName:'',
      str:''
    }
  },
  computed:{
    persions() {
      return this.$store.state.persionAbout.persionList
    },
    sum() {
      return this.$store.state.countAbout.sum
    },
    firstName() {
      return this.$store.getters['persionAbout/firstName']
    },
    serveStr() {
      return this.$store.state.persionAbout.serverStr
    },
  },
  methods: {
    add() {
      this.$store.commit('persionAbout/ADD_PERSION',{id:Date.now()+'_persion',name:this.inputName})
    },
    add_wang() {
      this.$store.dispatch('persionAbout/addWang',{id:Date.now()+'_persion',name:this.inputName})
    }  
  },
  mounted() {
    this.$store.dispatch('persionAbout/addForServe',{})
  }
}
</script>
```

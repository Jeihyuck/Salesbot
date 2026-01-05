<template>
    <v-row v-if="envStore.isMobile" class="d-flex justify-center" style="margin-top: calc(20vh);">
    <v-col class="ma-2">
      <v-row no-gutters class="mt-0 pt-0">
      <v-col>
        <!-- <img class="ml-12 pl-9" src="@/assets/samsung_logo.png" style="width: 280px; height: 70px"> -->
        <!-- <p class="ml-12 pl-13 mt-n2 mb-6 font-weight-black text-h5 black--text">{{project_name}} T/F </p> -->
      </v-col>
      </v-row>
        <v-spacer></v-spacer>
        <v-form class="mb-6 mt-2">
          <v-text-field
            variant="outlined"
            bg-color="#212121"
            label="ID"
            color="grey"
            v-model="username"
            prepend-inner-icon="mdi-email-outline"
          ></v-text-field>
            <v-text-field
            class="pt-2"
            variant="outlined"
            bg-color="#212121"
            color="grey"
            label="Password"
            type="password"
            v-model="password"
            prepend-inner-icon="mdi-lock-check-outline"
          ></v-text-field>
          <v-btn class="mt-8 text-subtitle-1" height="50px" depressed block color="primary" v-shortkey="['enter']" @shortkey="loginSubmit" @click="loginSubmit">Log In</v-btn>
          <!-- <v-btn class="mt-8 text-subtitle-1" height="50px" depressed block color="primary" @click="loginSubmit"> 로그인 </v-btn> -->
        <!-- <v-btn class="mt-8 text-subtitle-1" height="50px" depressed block color="primary" @click="loginSubmit"> 로그인 </v-btn> -->
        </v-form>
        <v-spacer></v-spacer>
    </v-col>
  </v-row>
  <!-- ###### PC ########################################### -->
    <v-row v-if="!envStore.isMobile" class="d-flex justify-center" style="margin-top: calc(10vh);">
    <v-col>
    </v-col>
    <v-col class="pr-16">
      <v-row no-gutters class="mt-0 pt-0">
      <v-col>
        <img class="ml-16 pl-10" src="@/assets/samsung_logo.png" style="width: 280px; height: 70px">
        <p class="ml-16 pl-14 mt-n4 mb-2 font-weight-black text-h5 black--text">Rubicon Admin</p>
      </v-col>
      </v-row>
        <v-spacer></v-spacer>
        <v-form class="mb-12 mt-2 ml-12 pl-12" style="width: 400px;">
          <v-text-field
            class="px-6"
            variant="outlined"
            bg-color="#212121"
            label="ID"
            color="grey"
            v-model="username"
            prepend-inner-icon="mdi-email-outline"
          ></v-text-field>
            <v-text-field
            class="pt-0 px-6"
            variant="outlined"
            bg-color="#212121"
            color="grey"
            label="Password"
            type="password"
            v-model="password"
            prepend-inner-icon="mdi-lock-check-outline"
          ></v-text-field>
          <v-col v-if="!isDev" class="px-6 pb-0 mb-0 d-flex justify-center">
            <v-btn height="40px" block @click="getMFACode"><div style="color: #1976D2;">Get MFA Verification CODE</div></v-btn>
          </v-col>
          <v-otp-input
            v-if="!isDev"
            class="px-0 mx-0"
            v-model="mfaCode"
            variant="solo"
            focus-all
            focused
          ></v-otp-input>
          <v-col class="px-6 pb-0 mb-0 d-flex justify-center">
            <v-btn class="text-subtitle-1" height="50px" depressed block color="primary" v-shortkey="['enter']" @shortkey="loginSubmit" @click="loginSubmit">Log In</v-btn>
          </v-col class="d-flex justify-center">
        </v-form>
        <v-spacer></v-spacer>
    </v-col>
    <v-col class="d-none d-sm-flex">
      <img src="@/assets/main.png" class="pb-0 mt-16" style="width: 500px; height: 400px">
    </v-col>
    <v-col>
    </v-col>

  </v-row>
</template>

<script setup>

import { ref, watch, getCurrentInstance, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router' 
import { useAuthStore } from '@/stores/auth'
import { useMenuStore } from '@/stores/menu'
import { useEnvStore } from '@/stores/env'
// import { use } from 'vue/types/umd';
import { alphaAuth } from '@/_services'
import { proxyRefs } from 'vue'
import CryptoJS from 'crypto-js'

const route = useRoute();
const router = useRouter()
const envStore = useEnvStore()

const project_name = import.meta.env.VITE_PROJECT_NAME
const encryptionKey = CryptoJS.enc.Utf8.parse(import.meta.env.VITE_ENCRYPTION_KEY)
const isDev = import.meta.env.VITE_OP_TYPE === 'DEV'
const username = ref('')
const password = ref('')
const encryptedPassword = ref('')
const mfaCode = ref('')
const loginSuccess = ref(false)
const loginFail = ref(false)

const authStore = useAuthStore()

// If already authenticated (e.g., dev bypass), go straight to /chat
onMounted(async () => {
  if (authStore.isAuthenticated) {
    await menuStore.getMenuList()
    router.push('/chat')
  }
})

watch(() => authStore.isAuthenticated, async (val) => {
  if (val) {
    await menuStore.getMenuList()
    router.push('/chat')
  }
}, { immediate: true })

watch(loginSuccess, () => {
loginFail.value = loginSuccess.value === 'false'
})

const getFormUpperClass = () => {
  if (!envStore.isMobile) {
    return "px-2"
  } else {
    return 'pr=16'
  }
}

const { proxy } = getCurrentInstance()
const menuStore = useMenuStore()

const getMFACode = async () => {
  const salt_response = await alphaAuth.misc.getOneTimeSalt(username.value)
  console.log('one_time_salt:', salt_response.data.one_time_salt)
  const saltedPassword = salt_response.data.one_time_salt + password.value
  console.log('Salted Password:', saltedPassword)

  encryptedPassword.value = await encrypt(saltedPassword, encryptionKey)
  alphaAuth.misc.mfa(username.value, encryptedPassword.value).then((response) => {
    console.log('MFA Code Response:', response)
  })
}

const encrypt = async (text, key) => {
  return CryptoJS.AES.encrypt(text, key, {mode: CryptoJS.mode.ECB}).toString();
}

const decrypt = async (ciphertext, key) => {
  const bytes = CryptoJS.AES.decrypt(ciphertext, key, {mode: CryptoJS.mode.ECB});
  return bytes.toString(CryptoJS.enc.Utf8);
}

const get_one_time_salt = async () => {
  const response = await alphaAuth.misc.salt()
  return response.data
}

const loginSubmit = async () => {
  const salt_response = await alphaAuth.misc.getOneTimeSalt(username.value)
  console.log('one_time_salt:', salt_response.data.one_time_salt)
  const saltedPassword = salt_response.data.one_time_salt + password.value
  console.log('Salted Password:', saltedPassword)
  encryptedPassword.value = await encrypt(saltedPassword, encryptionKey)
  console.log(encryptedPassword.value)
  if (!isDev && mfaCode.value.length < 6) {
    proxy.$snackbar.showSnackbar({
      title: 'Comment',
      message: 'Please enter a valid MFA code.',
      color: 'warning'
    })
  } else {
    if (isDev) {
      mfaCode.value = '000000'
    }
    await authStore.login(username.value, encryptedPassword.value, mfaCode.value, '-')

    if (authStore.isAuthenticated) {
      await menuStore.getMenuList()
      await router.push('/chat')
    } else {
      proxy.$snackbar.showSnackbar({
        title: 'Incorrect Login',
        message: 'Login information is not correct, check your ID and Password',
        color: 'error',
        timeout: 3000,
      })
    }
  }
}
</script>


<style lang="scss">
.login-text-input-field> div.v-input__control > div.v-input__slot {
  background-color: #2D2D2D !important;
}
.login-text-input-field> div.v-input__control > div.v-input__slot > div > input {
  color: #FFFFFF !important;
  padding-left: 6px;
}
.login-text-input-field> div.v-input__control > div.v-input__slot > div > .v-label {
  color: #FFFFFF !important;
  padding-left: 6px;
}
#app > div > div > div > form > div > div > div.v-input__slot > div.v-input__prepend-inner > div > .v-icon {
  color: white !important;
}
</style>

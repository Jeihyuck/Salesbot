<template>
  <v-row class="mt-4 pt-0 d-flex justify-center">
    <v-col></v-col>
    <v-col class="pr-16">
      <v-row no-gutters class="mt-0 pt-0">
        <v-col>
          <!-- <img class="ml-12 pl-9" src="@/assets/samsung_logo.png" style="width: 280px; height: 70px">
          <p class="ml-12 pl-13 mt-n2 mb-0 font-weight-black text-h5 black--text">{{ project_name }}</p> -->
          <p class="ml-12 pl-13 mb-0 font-weight-black text-h5 black--text">User Registration</p>
        </v-col>
      </v-row>
      <v-spacer></v-spacer>
      <v-form class="mb-12 mt-8 ml-12 pl-12" style="width: 400px;">
        <v-text-field
          variant="outlined"
          bg-color="#212121"
          label="ID (E-mail)"
          density="compact"
          color="grey"
          v-model="id"
          prepend-inner-icon="mdi-account-outline"
        ></v-text-field>
        <v-text-field
          class="pt-0 mt-n2"
          variant="outlined"
          bg-color="#212121"
          density="compact"
          label="User Name"
          color="grey"
          v-model="username"
          prepend-inner-icon="mdi-account-badge-outline"
        ></v-text-field>
        <v-combobox
          variant="outlined"
          class="pt-0 mt-n2"
          bg-color="#212121"
          hide-details
          density="compact"
          label="Department"
          :items="departments"
          prepend-inner-icon="mdi-account-group-outline"
          v-model="selectedDepartment"
        ></v-combobox>
        <v-text-field
          class="mt-2 pt-1"
          variant="outlined"
          bg-color="#212121"
          color="grey"
          label="Password"
          type="password"
          v-model="password"
          density="compact"
          prepend-inner-icon="mdi-lock-check-outline"
        ></v-text-field>
        <v-text-field
          class="pt-0 mt-n2"
          variant="outlined"
          bg-color="#212121"
          color="grey"
          label="Confirm Password"
          type="password"
          density="compact"
          v-model="confirmPassword"
          prepend-inner-icon="mdi-lock-check-outline"
        ></v-text-field>
        <v-btn
          class="mt-1 text-subtitle-1"
          height="50px"
          depressed
          block
          density="compact"
          color="primary"
          @click="registerSubmit"
        >
          Register
        </v-btn>
      </v-form>
      <v-spacer></v-spacer>
    </v-col>
    <v-col></v-col>
  </v-row>
</template>

<script setup>
import { ref } from 'vue'
import { alphaAuth } from '@/_services';

const project_name = import.meta.env.VITE_PROJECT_NAME
const id = ref('')
const username = ref('')
const department = ref('')
const password = ref('')
const confirmPassword = ref('')
const selectedDepartment = ref('')
const departments = ref([])

const { proxy } = getCurrentInstance()
const registerSubmit = () => {
  if (password.value !== confirmPassword.value) {
    // Handle password mismatch
    proxy.$snackbar.showSnackbar({
      title: 'Check your password',
      message: 'Please check your password, it does not match',
      color: 'warning'
    });
    return
  }
  const query = {
    id: id.value,
    username: username.value,
    department: selectedDepartment.value,
    password: password.value
  }
  alphaAuth.account.userFunction('create_user', query).then(response => {
    if (response.success) {
      // Handle successful registration
      proxy.$snackbar.showSnackbar({
        title: 'Registration successful',
        message: 'User has been successfully registered',
        color: 'success'
      });
    } else {
      // Handle registration failure
      proxy.$snackbar.showSnackbar({
        title: 'Registration failed',
        message: 'User registration has failed, please try again',
        color: 'error'
      });
    }
  })
  // Proceed with registration logic
  alert('Registration successful!')
}

onMounted(() => {
  alphaAuth.meta.department('listDepartment').then((response)=> {
    console.log(response.data)
    departments.value = response.data
  })
});


</script>

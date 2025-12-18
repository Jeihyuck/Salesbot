<template>
  <!-- <v-app>
    <v-container grow > -->
    <v-row class="mt-16 pt-16 d-flex justify-center">
    <v-col>
    </v-col>
    <v-col class="pr-16">
      <v-row no-gutters class="mt-0 pt-0">
      <v-col>
        <img class="ml-12 pl-9" src="@/assets/samsung_logo.png" style="width: 280px; height: 70px">
        <p class="ml-12 pl-13 mt-n2 mb-6 font-weight-black text-h5 black--text">{{project_name}} T/F </p>
      </v-col>
      </v-row>
        <v-spacer></v-spacer>
        <v-form class="mb-12 mt-8 ml-12 pl-12" style="width: 400px;">
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
          <v-btn class="mt-8 text-subtitle-1" height="50px" depressed block color="primary" v-shortkey="['enter']" @shortkey="loginSubmit" @click="loginSubmit">User Registration</v-btn>

        </v-form>
        <v-spacer></v-spacer>
    </v-col>

    <v-col>
    </v-col>

  </v-row>
</template>

<script setup>

import { ref } from 'vue'


const project_name = import.meta.env.VITE_PROJECT_NAME
const username = ref('')
const password = ref('')

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

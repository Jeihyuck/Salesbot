<template>
  <!-- ######## Below Code is for Mobile ############################################################################################################################################### -->
  <v-row>
    <v-btn @click="run">Run</v-btn>
  </v-row>
</template>

<script setup>
import axios from 'axios'

function run() {
  console.log('run');
  const url = 'api/rubicon/supplementaryinfo/';

  // ##############################################################
  const imageParams = {
    supplementType: 'media_image',
    messageId: 'a984dbb8-842c-4165-9842-67659c6f8375',
    supplementCount: 3,
  };
  axios.post(url, imageParams)
    .then(response => {
      console.log('Success:', response.data);
    })
    .catch(error => {
      console.error('Error:', error);
    });
  // ##############################################################
  const videoParams = {
    supplementType: 'media_video',
    messageId: 'a984dbb8-842c-4165-9842-67659c6f8375',
    supplementCount: 1,
  };
  axios.post(url, videoParams)
    .then(response => {
      console.log('Success:', response.data);
    })
    .catch(error => {
      console.error('Error:', error);
    });
  // ##############################################################
  const relatedQueryParams = {
    supplementType: 'related_query',
    messageId: 'a984dbb8-842c-4165-9842-67659c6f8375',
    supplementCount: 3,
  };
  axios.post(url, relatedQueryParams)
    .then(response => {
      console.log('Success:', response.data);
    })
    .catch(error => {
      console.error('Error:', error);
    });
  // ##############################################################
  const productCardParams = {
    supplementType: 'product_card',
    messageId: 'a984dbb8-842c-4165-9842-67659c6f8375',
    supplementCount: 3,
  };
  axios.post(url, productCardParams)
    .then(response => {
      console.log('Success:', response.data);
    })
    .catch(error => {
      console.error('Error:', error);
    });

}

</script>


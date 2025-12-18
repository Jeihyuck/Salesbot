<template>
  <v-container fluid :style="{ background: $vuetify.theme.themes.light.background }">
    <div> v-container : Grid 시스템에서 가장 큰 개체. 안에 layout 및 flex 를 포함</div>
    <v-divider class="py-2"></v-divider>
    <v-container fluid>
    전체 너비를 이용하고자 할 경우 fluid 전달
    </v-container>

    <div class="pt-8">inline : display 속성이 inline으로 지정된 엘리먼트는 전후 줄바꿈 없이 한 줄에 다른 엘리먼트들과 나란히 배치.</div>
    <div>blcok : display 속성이 block으로 지정된 엘리먼트는 전후 줄바꿈이 들어가 다른 엘리먼트들을 다른 줄로 밀어내고 혼자 한 줄을 차지. block 엘리먼트로 div이나 p, h1 태그 등.</div>
    <div>d-flex : 한 row를 block 형태로 차지.</div>
    <div class="pt-8"> Row Left / Right Align</div>
    <v-divider class="py-2"></v-divider>
    <v-container fluid>
      <v-row class="d-flex flex-row">
        <div class="item">Item #1</div>
        <div class="item">Item #2</div>
        <div class="item">Item #3</div>
      </v-row>
    </v-container>
    <v-container fluid>
      <v-row class="d-flex flex-row-reverse">
        <div class="item">Item #1</div>
        <div class="item">Item #2</div>
        <div class="item">Item #3</div>
      </v-row>
    </v-container>

    <div class="pt-8"> Column Top / Down Align </div>
    <v-divider class="py-2"></v-divider>
    <v-container fluid>
      <v-row class="d-flex flex-column">
        <div class="item">Item #1</div>
        <div class="item">Item #2</div>
        <div class="item">Item #3</div>
      </v-row>
    </v-container>
    <v-container fluid>
      <v-row class="d-flex flex-column-reverse">
        <div class="item">Item #1</div>
        <div class="item">Item #2</div>
        <div class="item">Item #3</div>
      </v-row>
    </v-container>

    <div class="pt-8">justify-start, end, center, space-between, space-around</div>
    <div class="pt-8"> Justify : Horizontal</div>
    <v-divider class="py-2"></v-divider>
    <v-container fluid>
      <v-row class="justify-start">
        <div class="item">Item #1</div>
        <div class="item">Item #2</div>
        <div class="item">Item #3</div>
      </v-row>
    </v-container>
    <v-container fluid>
      <v-row class="justify-center">
        <div class="item">Item #1</div>
        <div class="item">Item #2</div>
        <div class="item">Item #3</div>
      </v-row>
    </v-container>

    <div class="pt-8">align-start, end, center, baseline, stretch</div>
    <div class="pt-8"> Align : Vertical</div>
    <v-divider class="py-2"></v-divider>
    <v-container fluid style="height: 120px;">
        <v-row class="align-start" style="height: 120px;">
          <div class="item">Item #1</div>
          <div class="item">Item #2</div>
          <div class="item">Item #3</div>
        </v-row>
      </v-container>
    <v-container fluid style="height: 120px;">
        <v-row class="align-center" style="height: 120px;">
          <div class="item">Item #1</div>
          <div class="item">Item #2</div>
          <div class="item">Item #3</div>
        </v-row>
    </v-container>

    <div class="pt-8"> Center</div>
    <v-divider class="py-2"></v-divider>
    <v-container fluid style="height: 120px;">
        <v-row class="ma-0 align-center justify-center fill-height">
          <div class="item">Item #1</div>
          <div class="item">Item #2</div>
          <div class="item">Item #3</div>
        </v-row>
    </v-container>

    <div class="pt-8">align content</div>
    <v-divider class="py-2"></v-divider>
    <v-container fluid style="height: 120px;">
        <v-row class="ma-0 align-content-center justify-center fill-height">
          <div class="item">Item #1</div>
          <div class="item">Item #2</div>
          <div class="item">Item #3</div>
        </v-row>
    </v-container>

    <div class="pt-8">align self</div>
    <v-divider class="py-2"></v-divider>
    <v-container fluid style="height: 120px;">
        <v-row class="ma-0 fill-height">
          <div class="item align-self-start">Item #1</div>
          <div class="item align-self-center">Item #2</div>
          <div class="item">Item #3</div>
        </v-row>
    </v-container>
  </v-container>
</template>

<script lang='ts'>
</script>

<style scoped>
.container {
  border: 1px solid green;
}

.item {
  border: 1px solid blue;
}
</style>

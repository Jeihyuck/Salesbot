export const MyPlugin = {
  install(app) {
    app.config.globalProperties.sayHello = () => {
      console.log("Hello from MyPlugin!");
    };
  },
};
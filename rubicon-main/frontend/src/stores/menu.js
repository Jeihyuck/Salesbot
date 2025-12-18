import { defineStore } from 'pinia'
import { alpha } from '@/_services'

export const useMenuStore = defineStore('menu', {
    state: () => ({
      menuList: [],
      menuTree: [],
      menuPageTitle: {}
    }),
    actions: {
      async getMenuList () {
        // console.log('pinia login called')
        this.menuTree = []
        this.menuList = []
        await alpha.menu.getMenuList()
          .then((response) => {
            // console.log(response.data)
            const menuMap = {};
          
            response.data.forEach((item) => {
              // console.log(item)
              this.menuList.push(item)
              menuMap[item.id] = { ...item, children: [] };
              this.menuPageTitle[item.url] = item.page_title
            });
          
            response.data.forEach((item) => {
              if (item.parent_menu__id) {
                if (menuMap[item.parent_menu__id]) {
                  menuMap[item.parent_menu__id].children.push(menuMap[item.id]);
                }
              } else {
                this.menuTree.push(menuMap[item.id]);
              }
            })
          })
      }
      // async buildMenuTree(response.data) {
      //   console.log(menuItems)
      //   const menuMap = {};
      
      //   menuItems.forEach((item) => {
      //     console.log(item)
      //     menuMap[item.id] = { ...item, children: [] };
      //   });
      
      //   menuItems.forEach((item) => {
      //     if (item.parent_menu__id) {
      //       if (menuMap[item.parent_menu__id]) {
      //         menuMap[item.parent_menu__id].children.push(menuMap[item.id]);
      //       }
      //     } else {
      //       this.menuTree.push(menuMap[item.id]);
      //     }
      //   });
      // }
    },
    persist: true,
  })


  function buildMenuTree(menuItems) {
    const menuMap = {};
    const tree = [];
  
    menuItems.forEach((item) => {
      menuMap[item.id] = { ...item, children: [] };
    });
  
    menuItems.forEach((item) => {
      if (item.parent_menu__id) {
        if (menuMap[item.parent_menu__id]) {
          menuMap[item.parent_menu__id].children.push(menuMap[item.id]);
        }
      } else {
        tree.push(menuMap[item.id]);
      }
    });
  
    return tree;
  }
# Vue 文件夹重组 old -> new 明细（优化1）

> 来源提交：`fb15663`（等价复现 `vue优化1`）

> 说明：以下仅包含 **路径迁移（rename/move）** 项，格式为 `old -> new`。

## Layout 目录迁移

- yolo_weed_detection_vue/src/layout/component/aside.vue -> yolo_weed_detection_vue/src/components/layout/component/aside.vue
- yolo_weed_detection_vue/src/layout/component/columnsAside.vue -> yolo_weed_detection_vue/src/components/layout/component/columnsAside.vue
- yolo_weed_detection_vue/src/layout/component/header.vue -> yolo_weed_detection_vue/src/components/layout/component/header.vue
- yolo_weed_detection_vue/src/layout/component/main.vue -> yolo_weed_detection_vue/src/components/layout/component/main.vue
- yolo_weed_detection_vue/src/layout/footer/index.vue -> yolo_weed_detection_vue/src/components/layout/footer/index.vue
- yolo_weed_detection_vue/src/layout/index.vue -> yolo_weed_detection_vue/src/components/layout/index.vue
- yolo_weed_detection_vue/src/layout/lockScreen/index.vue -> yolo_weed_detection_vue/src/components/layout/lockScreen/index.vue
- yolo_weed_detection_vue/src/layout/logo/index.vue -> yolo_weed_detection_vue/src/components/layout/logo/index.vue
- yolo_weed_detection_vue/src/layout/main/classic.vue -> yolo_weed_detection_vue/src/components/layout/main/classic.vue
- yolo_weed_detection_vue/src/layout/main/columns.vue -> yolo_weed_detection_vue/src/components/layout/main/columns.vue
- yolo_weed_detection_vue/src/layout/main/defaults.vue -> yolo_weed_detection_vue/src/components/layout/main/defaults.vue
- yolo_weed_detection_vue/src/layout/main/transverse.vue -> yolo_weed_detection_vue/src/components/layout/main/transverse.vue
- yolo_weed_detection_vue/src/layout/navBars/breadcrumb/breadcrumb.vue -> yolo_weed_detection_vue/src/components/layout/navBars/breadcrumb/breadcrumb.vue
- yolo_weed_detection_vue/src/layout/navBars/breadcrumb/closeFull.vue -> yolo_weed_detection_vue/src/components/layout/navBars/breadcrumb/closeFull.vue
- yolo_weed_detection_vue/src/layout/navBars/breadcrumb/index.vue -> yolo_weed_detection_vue/src/components/layout/navBars/breadcrumb/index.vue
- yolo_weed_detection_vue/src/layout/navBars/breadcrumb/search.vue -> yolo_weed_detection_vue/src/components/layout/navBars/breadcrumb/search.vue
- yolo_weed_detection_vue/src/layout/navBars/breadcrumb/setings.vue -> yolo_weed_detection_vue/src/components/layout/navBars/breadcrumb/setings.vue
- yolo_weed_detection_vue/src/layout/navBars/breadcrumb/user.vue -> yolo_weed_detection_vue/src/components/layout/navBars/breadcrumb/user.vue
- yolo_weed_detection_vue/src/layout/navBars/index.vue -> yolo_weed_detection_vue/src/components/layout/navBars/index.vue
- yolo_weed_detection_vue/src/layout/navBars/tagsView/contextmenu.vue -> yolo_weed_detection_vue/src/components/layout/navBars/tagsView/contextmenu.vue
- yolo_weed_detection_vue/src/layout/navBars/tagsView/tagsView.vue -> yolo_weed_detection_vue/src/components/layout/navBars/tagsView/tagsView.vue
- yolo_weed_detection_vue/src/layout/navMenu/horizontal.vue -> yolo_weed_detection_vue/src/components/layout/navMenu/horizontal.vue
- yolo_weed_detection_vue/src/layout/navMenu/subItem.vue -> yolo_weed_detection_vue/src/components/layout/navMenu/subItem.vue
- yolo_weed_detection_vue/src/layout/navMenu/vertical.vue -> yolo_weed_detection_vue/src/components/layout/navMenu/vertical.vue
- yolo_weed_detection_vue/src/layout/routerView/iframes.vue -> yolo_weed_detection_vue/src/components/layout/routerView/iframes.vue
- yolo_weed_detection_vue/src/layout/routerView/link.vue -> yolo_weed_detection_vue/src/components/layout/routerView/link.vue
- yolo_weed_detection_vue/src/layout/routerView/parent.vue -> yolo_weed_detection_vue/src/components/layout/routerView/parent.vue
- yolo_weed_detection_vue/src/layout/upgrade/index.vue -> yolo_weed_detection_vue/src/components/layout/upgrade/index.vue

## Styles 目录迁移

- yolo_weed_detection_vue/src/theme/app.scss -> yolo_weed_detection_vue/src/styles/app.scss
- yolo_weed_detection_vue/src/theme/common/transition.scss -> yolo_weed_detection_vue/src/styles/common/transition.scss
- yolo_weed_detection_vue/src/theme/dark.scss -> yolo_weed_detection_vue/src/styles/dark.scss
- yolo_weed_detection_vue/src/theme/element.scss -> yolo_weed_detection_vue/src/styles/element.scss
- yolo_weed_detection_vue/src/theme/fonts/iconfont.css -> yolo_weed_detection_vue/src/styles/fonts/iconfont.css
- yolo_weed_detection_vue/src/theme/fonts/iconfont.js -> yolo_weed_detection_vue/src/styles/fonts/iconfont.js
- yolo_weed_detection_vue/src/theme/fonts/iconfont.json -> yolo_weed_detection_vue/src/styles/fonts/iconfont.json
- yolo_weed_detection_vue/src/theme/fonts/iconfont.ttf -> yolo_weed_detection_vue/src/styles/fonts/iconfont.ttf
- yolo_weed_detection_vue/src/theme/iconSelector.scss -> yolo_weed_detection_vue/src/styles/iconSelector.scss
- yolo_weed_detection_vue/src/theme/index.scss -> yolo_weed_detection_vue/src/styles/index.scss
- yolo_weed_detection_vue/src/theme/loading.scss -> yolo_weed_detection_vue/src/styles/loading.scss
- yolo_weed_detection_vue/src/theme/media/chart.scss -> yolo_weed_detection_vue/src/styles/media/chart.scss
- yolo_weed_detection_vue/src/theme/media/cityLinkage.scss -> yolo_weed_detection_vue/src/styles/media/cityLinkage.scss
- yolo_weed_detection_vue/src/theme/media/date.scss -> yolo_weed_detection_vue/src/styles/media/date.scss
- yolo_weed_detection_vue/src/theme/media/dialog.scss -> yolo_weed_detection_vue/src/styles/media/dialog.scss
- yolo_weed_detection_vue/src/theme/media/error.scss -> yolo_weed_detection_vue/src/styles/media/error.scss
- yolo_weed_detection_vue/src/theme/media/form.scss -> yolo_weed_detection_vue/src/styles/media/form.scss
- yolo_weed_detection_vue/src/theme/media/home.scss -> yolo_weed_detection_vue/src/styles/media/home.scss
- yolo_weed_detection_vue/src/theme/media/index.scss -> yolo_weed_detection_vue/src/styles/media/index.scss
- yolo_weed_detection_vue/src/theme/media/layout.scss -> yolo_weed_detection_vue/src/styles/media/layout.scss
- yolo_weed_detection_vue/src/theme/media/login.scss -> yolo_weed_detection_vue/src/styles/media/login.scss
- yolo_weed_detection_vue/src/theme/media/media.scss -> yolo_weed_detection_vue/src/styles/media/media.scss
- yolo_weed_detection_vue/src/theme/media/pagination.scss -> yolo_weed_detection_vue/src/styles/media/pagination.scss
- yolo_weed_detection_vue/src/theme/media/personal.scss -> yolo_weed_detection_vue/src/styles/media/personal.scss
- yolo_weed_detection_vue/src/theme/media/scrollbar.scss -> yolo_weed_detection_vue/src/styles/media/scrollbar.scss
- yolo_weed_detection_vue/src/theme/media/tagsView.scss -> yolo_weed_detection_vue/src/styles/media/tagsView.scss
- yolo_weed_detection_vue/src/theme/mixins/index.scss -> yolo_weed_detection_vue/src/styles/mixins/index.scss
- yolo_weed_detection_vue/src/theme/other.scss -> yolo_weed_detection_vue/src/styles/other.scss
- yolo_weed_detection_vue/src/theme/tableTool.scss -> yolo_weed_detection_vue/src/styles/tableTool.scss
- yolo_weed_detection_vue/src/theme/waves.scss -> yolo_weed_detection_vue/src/styles/waves.scss

## I18n/Stores/Types/Config 迁移

- yolo_weed_detection_vue/src/i18n/index.ts -> yolo_weed_detection_vue/src/utils/i18n/index.ts
- yolo_weed_detection_vue/src/i18n/lang/en.ts -> yolo_weed_detection_vue/src/utils/i18n/lang/en.ts
- yolo_weed_detection_vue/src/i18n/lang/zh-cn.ts -> yolo_weed_detection_vue/src/utils/i18n/lang/zh-cn.ts
- yolo_weed_detection_vue/src/i18n/lang/zh-tw.ts -> yolo_weed_detection_vue/src/utils/i18n/lang/zh-tw.ts
- yolo_weed_detection_vue/src/i18n/pages/formI18n/en.ts -> yolo_weed_detection_vue/src/utils/i18n/pages/formI18n/en.ts
- yolo_weed_detection_vue/src/i18n/pages/formI18n/zh-cn.ts -> yolo_weed_detection_vue/src/utils/i18n/pages/formI18n/zh-cn.ts
- yolo_weed_detection_vue/src/i18n/pages/formI18n/zh-tw.ts -> yolo_weed_detection_vue/src/utils/i18n/pages/formI18n/zh-tw.ts
- yolo_weed_detection_vue/src/i18n/pages/login/en.ts -> yolo_weed_detection_vue/src/utils/i18n/pages/login/en.ts
- yolo_weed_detection_vue/src/i18n/pages/login/zh-cn.ts -> yolo_weed_detection_vue/src/utils/i18n/pages/login/zh-cn.ts
- yolo_weed_detection_vue/src/i18n/pages/login/zh-tw.ts -> yolo_weed_detection_vue/src/utils/i18n/pages/login/zh-tw.ts
- yolo_weed_detection_vue/src/config/imageConfig.ts -> yolo_weed_detection_vue/src/utils/imageConfig.ts
- yolo_weed_detection_vue/src/stores/index.ts -> yolo_weed_detection_vue/src/utils/stores/index.ts
- yolo_weed_detection_vue/src/stores/keepAliveNames.ts -> yolo_weed_detection_vue/src/utils/stores/keepAliveNames.ts
- yolo_weed_detection_vue/src/stores/requestOldRoutes.ts -> yolo_weed_detection_vue/src/utils/stores/requestOldRoutes.ts
- yolo_weed_detection_vue/src/stores/routesList.ts -> yolo_weed_detection_vue/src/utils/stores/routesList.ts
- yolo_weed_detection_vue/src/stores/tagsViewRoutes.ts -> yolo_weed_detection_vue/src/utils/stores/tagsViewRoutes.ts
- yolo_weed_detection_vue/src/stores/themeConfig.ts -> yolo_weed_detection_vue/src/utils/stores/themeConfig.ts
- yolo_weed_detection_vue/src/stores/userInfo.ts -> yolo_weed_detection_vue/src/utils/stores/userInfo.ts
- yolo_weed_detection_vue/src/types/axios.d.ts -> yolo_weed_detection_vue/src/utils/types/axios.d.ts
- yolo_weed_detection_vue/src/types/global.d.ts -> yolo_weed_detection_vue/src/utils/types/global.d.ts
- yolo_weed_detection_vue/src/types/layout.d.ts -> yolo_weed_detection_vue/src/utils/types/layout.d.ts
- yolo_weed_detection_vue/src/types/mitt.d.ts -> yolo_weed_detection_vue/src/utils/types/mitt.d.ts
- yolo_weed_detection_vue/src/types/pinia.d.ts -> yolo_weed_detection_vue/src/utils/types/pinia.d.ts
- yolo_weed_detection_vue/src/types/views.d.ts -> yolo_weed_detection_vue/src/utils/types/views.d.ts

## Views 页面迁移

- yolo_weed_detection_vue/src/views/cameraPredict/index.vue -> yolo_weed_detection_vue/src/views/Detect/Camera/index.vue
- yolo_weed_detection_vue/src/views/imgPredict/index.vue -> yolo_weed_detection_vue/src/views/Detect/Image/index.vue
- yolo_weed_detection_vue/src/views/videoPredict/index.vue -> yolo_weed_detection_vue/src/views/Detect/Video/index.vue
- yolo_weed_detection_vue/src/views/cameraRecord/index.vue -> yolo_weed_detection_vue/src/views/History/Camera/index.vue
- yolo_weed_detection_vue/src/views/imgRecord/index.vue -> yolo_weed_detection_vue/src/views/History/Image/index.vue
- yolo_weed_detection_vue/src/views/videoRecord/index.vue -> yolo_weed_detection_vue/src/views/History/Video/index.vue
- yolo_weed_detection_vue/src/views/videoRecord/show.vue -> yolo_weed_detection_vue/src/views/History/Video/show.vue
- yolo_weed_detection_vue/src/views/personal/index.vue -> yolo_weed_detection_vue/src/views/UserCenter/Profile/index.vue
- yolo_weed_detection_vue/src/views/userManage/dialog.vue -> yolo_weed_detection_vue/src/views/UserCenter/UserManage/dialog.vue
- yolo_weed_detection_vue/src/views/userManage/index.vue -> yolo_weed_detection_vue/src/views/UserCenter/UserManage/index.vue


---
总计迁移文件：92

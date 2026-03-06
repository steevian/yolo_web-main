<template>
	<div class="layout-logo" v-if="setShowLogo" @click="onThemeConfigChange">
		<div class="logo-img-wrap">
			<img :src="logoMini" class="layout-logo-medium-img" />
		</div>
		<span>安徽农业大学</span>
	</div>
	<div class="layout-logo-size" v-else @click="onThemeConfigChange">
		<div class="logo-img-wrap logo-img-wrap--small">
			<img :src="logoMini" class="layout-logo-size-img" />
		</div>
	</div>
</template>

<script setup lang="ts" name="layoutLogo">
import { computed } from 'vue';
import { storeToRefs } from 'pinia';
import { useThemeConfig } from '@/utils/stores/themeConfig';
import logoMini from '@/assets/logo-mini.svg';

// 定义变量内容
const storesThemeConfig = useThemeConfig();
const { themeConfig } = storeToRefs(storesThemeConfig);

// 设置 logo 的显示。classic 经典布局默认显示 logo
const setShowLogo = computed(() => {
	let { isCollapse, layout } = themeConfig.value;
	return !isCollapse || layout === 'classic' || document.body.clientWidth < 1000;
});
// logo 点击实现菜单展开/收起
const onThemeConfigChange = () => {
	if (themeConfig.value.layout === 'transverse') return false;
	themeConfig.value.isCollapse = !themeConfig.value.isCollapse;
};
</script>

<style scoped lang="scss">
.layout-logo {
	width: calc(100% - 8px);
	min-height: 124px;
	margin: 4px auto 10px;
	padding: 18px 12px 12px;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	gap: 12px;
	background: #2a2e37;
	border-radius: 16px;
	box-shadow: 0 10px 24px rgba(15, 23, 42, 0.18);
	border: none;
	color: #fff;
	font-size: 18px;
	font-weight: 800;
	line-height: 1.2;
	cursor: pointer;
	animation: logoAnimation 0.3s ease-in-out;
	.logo-img-wrap {
		width: 62px;
		height: 62px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: #fff;
		border-radius: 50%;
		box-shadow: 0 2px 8px rgba(0,0,0,0.06);
		margin-bottom: 2px;
	}
	&-medium-img {
		width: 48px;
		height: 48px;
		object-fit: contain;
		image-rendering: -webkit-optimize-contrast;
		image-rendering: crisp-edges;
		display: block;
		margin: 0 auto;
	}
	span {
		white-space: nowrap;
		display: block;
		text-align: center;
		color: #fff;
		font-weight: 800;
		letter-spacing: 0.3px;
		margin-top: 2px;
		font-size: 17px;
	}
	&:hover {
		span {
			color: #fff;
		}
	}
}
.layout-logo-size {
	width: calc(100% - 8px);
	height: 76px;
	margin: 4px auto 10px;
	border-radius: 14px;
	background: #2a2e37;
	box-shadow: 0 10px 24px rgba(15, 23, 42, 0.18);
	display: flex;
	align-items: center;
	justify-content: center;
	cursor: pointer;
	animation: logoAnimation 0.3s ease-in-out;
	.logo-img-wrap--small {
		width: 44px;
		height: 44px;
		background: #fff;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 2px 8px rgba(0,0,0,0.06);
	}
	&-img {
		width: 28px;
		height: 28px;
		object-fit: contain;
		display: block;
		margin: 0 auto;
	}
	&:hover {
		img {
			animation: logoAnimation 0.3s ease-in-out;
		}
	}
}
</style>


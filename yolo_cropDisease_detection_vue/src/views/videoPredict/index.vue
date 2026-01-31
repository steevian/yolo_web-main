<template>
	<div class="system-predict-container layout-padding">
		<div class="system-predict-padding layout-padding-auto layout-padding-view">
			<div class="header">
				<!-- 仅保留置信度阈值设置，删除作物/模型下拉框 -->
				<div class="conf" style="display: flex; flex-direction: row; align-items: center;">
					<div
						style="font-size: 14px;margin-right: 20px;display: flex;justify-content: start;align-items: center;color: #909399;">
						设置最小置信度阈值
					</div>
					<el-slider v-model="conf" :format-tooltip="formatTooltip" style="width: 280px;" 
					  :min="0" :max="100" :step="1" />
				</div>
				<!-- 视频上传按钮，保留核心功能 -->
				<el-upload v-model="state.form.inputVideo" ref="uploadFile" class="avatar-uploader"
					:action="uploadAction" :show-file-list="false" :on-success="handleAvatarSuccessone"
					:disabled="state.isDetecting" :before-upload="beforeUpload">
					<div class="button-section" style="margin-left: 20px">
						<el-button type="info" class="predict-button" :disabled="state.isDetecting">上传杂草检测视频</el-button>
					</div>
				</el-upload>
				<!-- 开始检测按钮，修改文案为杂草检测，增加禁用逻辑 -->
				<div class="button-section" style="margin-left: 20px">
					<el-button type="primary" @click="upData" class="predict-button" :disabled="!state.form.inputVideo || state.isDetecting">
						{{ state.isDetecting ? '正在检测中' : '开始杂草检测' }}
					</el-button>
				</div>
				<!-- 进度条，修改文案为杂草检测适配 -->
				<div class="demo-progress" v-if="state.isShow">
					<el-progress :text-inside="true" :stroke-width="20" :percentage="state.percentage" style="width: 380px;">
						<span>{{ state.type_text }} {{ state.percentage }}%</span>
					</el-progress>
				</div>
			</div>
			<!-- 视频检测结果预览区域，保留核心功能，增加空状态提示 -->
			<div class="cards" ref="cardsContainer">
				<video 
					v-if="state.video_path && isVideoActive" 
					ref="videoPlayer"
					class="video" 
					:src="state.video_path" 
					controls 
					autoplay 
					muted 
					loop 
					alt="杂草检测视频结果"
					@loadedmetadata="onVideoLoaded"
					@error="onVideoError"
				></video>
				<div v-else class="empty-tip">
					<el-icon class="empty-icon"><VideoCamera /></el-icon>
					<div>请上传视频并点击「开始杂草检测」查看结果</div>
					<div class="empty-sub">支持MP4、AVI等常见视频格式</div>
				</div>
			</div>
			
			<!-- 状态提示 -->
			<el-alert
				v-if="statusMessage"
				:title="statusMessage"
				:type="statusType"
				show-icon
				closable
				@close="statusMessage = ''"
				style="margin-top: 15px;"
			/>
		</div>
	</div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted, onActivated, onDeactivated, onUnmounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { VideoCamera } from '@element-plus/icons-vue';
import request from '/@/utils/request';
import { useUserInfo } from '/@/stores/userInfo';
import { storeToRefs } from 'pinia';
import type { UploadInstance, UploadProps } from 'element-plus';
import { SocketService } from '/@/utils/socket';
import { formatDate } from '/@/utils/formatTime';

// 核心变量定义
const uploadFile = ref<UploadInstance>();
const conf = ref(50); // 置信度默认50%（0-100范围）
const stores = useUserInfo();
const { userInfos } = storeToRefs(stores);
const videoPlayer = ref<HTMLVideoElement | null>(null); // 视频播放器引用

// 状态管理
const isVideoActive = ref(false); // 视频是否正在播放
const statusMessage = ref(''); // 状态消息
const statusType = ref('info'); // 状态类型
const videoLoadAttempts = ref(0); // 视频加载尝试次数

// 跨域核心修复：自动获取当前页面IP，替换硬编码的localhost，解决路由切换/跨域问题
const currentHost = window.location.hostname;
// SpringBoot视频上传地址（跨域适配）
const uploadAction = ref(`http://${currentHost}:9999/files/upload`);

const state = reactive({
	video_path: '', // 检测结果视频地址
	type_text: "正在处理杂草检测视频", // 进度条文案
	percentage: 0, // 进度条百分比
	isShow: false, // 进度条显示状态
	isDetecting: false, // 检测状态锁，防止重复点击/请求
	form: { // 检测请求参数
		username: '',
		inputVideo: null as any, // 上传视频的后端标识
		conf: 0.5, // 置信度（默认0.5）
		startTime: '' // 检测时间
	},
});

// Socket通信核心修复
const socketService = new SocketService();

// 初始化Socket连接
const initSocket = () => {
	// 如果Socket已连接，先关闭
	if (socketService.connected) {
		socketService.close();
	}
	
	// 连接当前IP的Flask服务
	socketService.connect(`ws://${currentHost}:5000`);
	
	// Socket消息监听
	socketService.on('message', (data) => {
		console.log('Socket接收消息:', data);
		if (typeof data === 'object' && data.data) {
			ElMessage.success(data.data);
		} else {
			ElMessage.success(data);
		}
	});
	
	// 进度条监听
	socketService.on('progress', (data) => {
		if (typeof data === 'object' && data.data !== undefined) {
			state.percentage = parseInt(data.data);
		} else {
			state.percentage = parseInt(data);
		}
		
		if (state.percentage < 100) {
			state.isShow = true;
		} else {
			ElMessage.success("杂草检测视频处理完成！");
			setTimeout(() => {
				state.isShow = false;
				state.percentage = 0;
				state.isDetecting = false; // 处理完成后释放检测锁
				statusMessage.value = '视频检测完成，可以播放结果';
				statusType.value = 'success';
			}, 2000);
		}
		console.log('视频处理进度:', state.percentage);
	});
	
	// Socket错误监听
	socketService.on('error', (err) => {
		console.error('Socket连接错误:', err);
		ElMessage.error('实时进度通知连接失败，进度条将无法更新！');
		state.isDetecting = false;
		statusMessage.value = '实时通知连接失败，但视频检测仍在进行';
		statusType.value = 'warning';
	});
};

// 置信度滑块格式化（转成0-1的小数）
const formatTooltip = (val: number) => {
	return val / 100;
};

// 上传前验证
const beforeUpload = (file: File) => {
	// 检查文件类型
	const allowedTypes = ['video/mp4', 'video/avi', 'video/mpeg', 'video/quicktime', 'video/x-msvideo'];
	const isVideo = allowedTypes.some(type => file.type.startsWith('video/') || allowedTypes.includes(file.type));
	
	if (!isVideo) {
		ElMessage.error('只能上传视频文件（MP4、AVI等格式）！');
		return false;
	}
	
	// 检查文件大小（限制100MB）
	const isLt100M = file.size / 1024 / 1024 < 100;
	if (!isLt100M) {
		ElMessage.error('视频大小不能超过100MB！');
		return false;
	}
	
	return true;
};

// 视频上传成功回调
const handleAvatarSuccessone: UploadProps['onSuccess'] = (response, uploadFile) => {
	// 停止当前视频播放
	stopVideoPlayback();
	
	// 上传新视频，清空之前的检测结果，防止残留
	state.video_path = '';
	isVideoActive.value = false;
	state.form.inputVideo = response.data;
	ElMessage.success('杂草检测视频上传成功！');
	statusMessage.value = '视频上传成功，请点击开始检测';
	statusType.value = 'success';
};

// 停止视频播放
const stopVideoPlayback = () => {
	if (videoPlayer.value) {
		videoPlayer.value.pause();
		videoPlayer.value.src = '';
		videoPlayer.value.load();
	}
	isVideoActive.value = false;
};

// 视频加载完成
const onVideoLoaded = () => {
	console.log('视频加载完成');
	isVideoActive.value = true;
	videoLoadAttempts.value = 0;
	statusMessage.value = '视频加载完成，可以开始播放';
	statusType.value = 'success';
};

// 视频加载错误
const onVideoError = (error: Event) => {
	console.error('视频加载失败:', error);
	videoLoadAttempts.value++;
	
	if (videoLoadAttempts.value <= 3) {
		// 重试加载
		setTimeout(() => {
			if (videoPlayer.value && state.video_path) {
				videoPlayer.value.load();
			}
		}, 1000 * videoLoadAttempts.value);
	} else {
		statusMessage.value = '视频加载失败，请检查Flask服务或重新检测';
		statusType.value = 'error';
		isVideoActive.value = false;
		state.isDetecting = false;
	}
};

// 开始杂草检测
const upData = async () => {
	// 多重参数校验，防止非法请求
	if (state.isDetecting) return ElMessage.warning('正在处理视频，请勿重复点击！');
	if (!state.form.inputVideo) return ElMessage.warning('请先上传杂草检测视频！');
	if (isNaN(Number(conf.value)) || conf.value < 0 || conf.value > 100) return ElMessage.warning('请设置0-100之间的有效置信度阈值！');
	
	try {
		// 组装请求参数
		state.isDetecting = true; // 开启检测锁，防止重复请求
		state.form.conf = parseFloat(conf.value) / 100;
		state.form.username = userInfos.value.userName || 'default_user';
		state.form.startTime = formatDate(new Date(), 'YYYY-MM-DD HH:mm:ss');
		
		// 停止当前视频播放
		stopVideoPlayback();
		
		// 初始化Socket连接
		initSocket();
		
		// 等待Socket连接建立
		await new Promise(resolve => setTimeout(resolve, 500));
		
		console.log('杂草检测视频请求参数:', state.form);
		
		// 拼接请求地址
		const queryParams = new URLSearchParams({
			username: state.form.username,
			conf: state.form.conf.toString(),
			startTime: state.form.startTime,
			inputVideo: state.form.inputVideo
		}).toString();
		
		// 设置视频路径（添加时间戳避免缓存）
		const videoUrl = `http://${currentHost}:5000/predictVideo?${queryParams}&t=${Date.now()}`;
		state.video_path = videoUrl;
		
		// 重置视频加载尝试次数
		videoLoadAttempts.value = 0;
		
		// 显示进度条
		state.isShow = true;
		state.percentage = 0;
		
		ElMessage.info('正在加载杂草检测视频，请稍候...');
		statusMessage.value = '正在处理视频检测，请等待进度完成';
		statusType.value = 'info';
		
	} catch (error) {
		console.error('开始视频检测失败:', error);
		ElMessage.error('开始视频检测失败');
		statusMessage.value = '开始视频检测失败，请重试';
		statusType.value = 'error';
		state.isDetecting = false;
		state.isShow = false;
	}
};

// 重置页面状态
const resetPageState = () => {
	// 停止视频播放
	stopVideoPlayback();
	
	// 重置状态
	state.video_path = '';
	state.percentage = 0;
	state.isShow = false;
	state.isDetecting = false;
	state.form.inputVideo = null;
	isVideoActive.value = false;
	statusMessage.value = '';
	videoLoadAttempts.value = 0;
	
	// 清空上传组件的文件
	if (uploadFile.value) {
		uploadFile.value.clearFiles();
	}
	
	// 关闭Socket连接
	if (socketService && socketService.connected) {
		socketService.close();
	}
	
	console.log('视频检测页面状态已重置');
};

// 【路由切换核心修复】页面激活时：重置状态+重连Socket
onActivated(() => {
	console.log('视频检测页面激活');
	resetPageState();
	
	// 初始化Socket
	initSocket();
	
	// 恢复置信度设置
	state.form.conf = conf.value / 100;
});

// 【路由切换核心修复】页面失活时：销毁资源+关闭Socket
onDeactivated(() => {
	console.log('视频检测页面失活');
	resetPageState();
});

// 【路由切换核心修复】页面卸载时：最终资源清理
onUnmounted(() => {
	console.log('视频检测页面卸载');
	resetPageState();
});

// 页面挂载初始化
// 页面挂载初始化
onMounted(() => {
  // 检查Flask服务是否可用
  checkFlaskConnection();
  
  // 原有逻辑
  state.form.conf = conf.value / 100;
  
  // 初始化Socket连接
  initSocket();
});

// 添加Flask连接检查方法
const checkFlaskConnection = async () => {
  try {
    const response = await request.get('/flask/test');
    console.log('Flask连接正常:', response);
    statusMessage.value = 'Flask服务连接正常';
    statusType.value = 'success';
  } catch (error) {
    console.error('Flask连接失败:', error);
    ElMessage.error('Flask服务未启动，请确保已启动Flask后端服务');
    statusMessage.value = 'Flask服务未启动，无法进行视频检测';
    statusType.value = 'error';
  }
};
</script>

<style scoped lang="scss">
.system-predict-container {
	width: 100%;
	height: 100vh;
	display: flex;
	flex-direction: column;
	background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);

	.system-predict-padding {
		padding: 15px;
		height: 100%;
		display: flex;
		flex-direction: column;
	}
}

.header {
	width: 100%;
	display: flex;
	justify-content: start;
	align-items: center;
	font-size: 20px;
	flex-wrap: wrap;
	gap: 15px;
	padding-bottom: 15px;
	border-bottom: 2px solid #e5e7eb;
	margin-bottom: 20px;
	background: white;
	padding: 15px;
	border-radius: 10px;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.cards {
	width: 100%;
	flex: 1;
	border-radius: 12px;
	margin-top: 15px;
	padding: 20px;
	overflow: hidden;
	display: flex;
	justify-content: center;
	align-items: center;
	background: white;
	position: relative;
	min-height: 500px;
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);

	// 空状态提示样式
	.empty-tip {
		color: #606266;
		font-size: 18px;
		text-align: center;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 15px;
		
		.empty-icon {
			font-size: 64px;
			color: #c0c4cc;
			margin-bottom: 10px;
		}
		
		.empty-sub {
			font-size: 14px;
			color: #909399;
			margin-top: 5px;
		}
	}
}

// 修复：视频播放器样式
.video {
	width: 100%;
	max-height: 75vh;
	height: auto;
	object-fit: contain;
	border-radius: 8px;
	box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
	border: 2px solid #409eff;
	background: #000;
}

.button-section {
	display: flex;
	justify-content: center;
	min-width: 180px;
	
	.predict-button {
		width: 100%;
		padding: 10px 20px;
		font-size: 14px;
		border-radius: 6px;
		transition: all 0.3s ease;
		
		&:hover {
			transform: translateY(-2px);
			box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
		}
		
		&:disabled {
			opacity: 0.6;
			cursor: not-allowed;
			transform: none;
			box-shadow: none;
		}
	}
}

.demo-progress {
	min-width: 300px;
	background: white;
	padding: 10px;
	border-radius: 6px;
	box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

// 响应式适配优化
@media (max-width: 1400px) {
	.header {
		gap: 12px;
	}
	.demo-progress {
		width: 100%;
		margin-left: 0 !important;
		min-width: unset;
	}
	.button-section {
		min-width: 160px;
	}
}

@media (max-width: 992px) {
	.header {
		flex-direction: column;
		align-items: stretch;
		gap: 15px;
	}
	
	.conf {
		width: 100%;
		justify-content: space-between;
	}
	
	.el-slider {
		width: 100% !important;
	}
	
	.button-section {
		width: 100%;
		margin-left: 0 !important;
		min-width: unset;
	}
	
	.cards {
		min-height: 400px;
		padding: 15px;
	}
	
	.video {
		max-height: 65vh;
	}
}

@media (max-width: 768px) {
	.system-predict-padding {
		padding: 10px;
	}
	
	.cards {
		min-height: 350px;
		padding: 10px;
		
		.empty-tip {
			font-size: 16px;
			
			.empty-icon {
				font-size: 48px;
			}
		}
	}
	
	.video {
		max-height: 60vh;
	}
}
</style>
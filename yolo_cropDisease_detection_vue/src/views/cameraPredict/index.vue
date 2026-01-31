<template>
	<div class="system-predict-container layout-padding">
		<div class="system-predict-padding layout-padding-auto layout-padding-view">
			<div class="header">
				<div class="conf" style="display: flex; flex-direction: row; align-items: center;">
					<div style="font-size: 14px; margin-right: 20px; color: #909399;">
						设置最小置信度阈值
					</div>
					<el-slider v-model="conf" :format-tooltip="formatTooltip" style="width: 280px;" 
					  :min="0" :max="100" :step="1" />
				</div>
				<div class="button-section" style="margin-left: 20px">
					<el-button type="primary" @click="startCamera" class="predict-button" :disabled="isCameraActive || isStopping">
						{{ isCameraActive ? '检测中' : '开启摄像头检测' }}
					</el-button>
				</div>
                <div class="button-section" style="margin-left: 20px">
					<el-button type="warning" @click="stopCamera" class="predict-button" :disabled="!isCameraActive">
						关闭摄像头检测
					</el-button>
				</div>
				<div class="demo-progress" v-if="isProcessing">
					<el-progress :text-inside="true" :stroke-width="20" :percentage="progressPercentage" style="width: 380px; margin-left: 20px;">
						<span>{{ progressText }} {{ progressPercentage }}%</span>
					</el-progress>
				</div>
			</div>
			<div class="cards" ref="cardsContainer">
				<!-- 使用img标签显示MJPEG流 -->
				<img 
					v-if="isCameraActive && cameraStreamUrl" 
					class="video-stream" 
					:src="cameraStreamUrl" 
					alt="杂草检测摄像头实时流"
					@error="handleStreamError"
				/>
				<div v-else class="empty-tip">
					<el-icon class="empty-icon"><VideoCamera /></el-icon>
					<div>请点击「开启摄像头检测」启动实时杂草检测</div>
					<div class="empty-sub">摄像头检测不会自动录制，仅实时预览</div>
				</div>
			</div>
			
			<!-- 状态提示 -->
			<el-alert
				v-if="cameraStatusMessage"
				:title="cameraStatusMessage"
				:type="cameraStatusType"
				show-icon
				closable
				@close="cameraStatusMessage = ''"
				style="margin-top: 15px;"
			/>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, onMounted, onActivated, onDeactivated, onUnmounted, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { VideoCamera } from '@element-plus/icons-vue';
import request from '/@/utils/request';
import { useUserInfo } from '/@/stores/userInfo';
import { storeToRefs } from 'pinia';
import { formatDate } from '/@/utils/formatTime';

// 状态管理
const conf = ref(50);
const isCameraActive = ref(false);      // 摄像头是否激活
const isStopping = ref(false);          // 是否正在停止
const isProcessing = ref(false);        // 是否在处理中
const progressPercentage = ref(0);      // 进度百分比
const progressText = ref("正在处理视频");
const cameraStreamUrl = ref('');        // 摄像头流URL
const cameraStatusMessage = ref('');    // 状态消息
const cameraStatusType = ref('info');   // 状态类型
const streamImgRef = ref<HTMLImageElement | null>(null); // 视频流img引用

// 用户信息
const stores = useUserInfo();
const { userInfos } = storeToRefs(stores);
const currentHost = window.location.hostname;

// 表单数据
const formData = ref({
	username: '',
	conf: 0.5,
	startTime: ''
});

// 置信度滑块格式化
const formatTooltip = (val: number) => val / 100;

// 检查摄像头权限
const checkCameraPermission = async (): Promise<boolean> => {
	try {
		// 尝试访问摄像头
		const stream = await navigator.mediaDevices.getUserMedia({ 
			video: { width: 640, height: 480 } 
		});
		
		// 立即释放，我们只需要确认有权限
		stream.getTracks().forEach(track => track.stop());
		return true;
	} catch (error) {
		console.error('摄像头权限检查失败:', error);
		cameraStatusMessage.value = '摄像头权限被拒绝，请确保已授予摄像头权限';
		cameraStatusType.value = 'error';
		return false;
	}
};

// 开启摄像头检测
const startCamera = async () => {
	// 防止重复开启
	if (isCameraActive.value) {
		ElMessage.warning('摄像头检测已在运行中');
		return;
	}
	
	// 检查摄像头权限
	const hasPermission = await checkCameraPermission();
	if (!hasPermission) {
		return;
	}
	
	// 校验置信度
	if (isNaN(Number(conf.value)) || conf.value < 0 || conf.value > 100) {
		ElMessage.warning("请设置0-100之间的有效置信度阈值！");
		return;
	}
	
	try {
		// 更新状态
		isCameraActive.value = true;
		isStopping.value = false;
		isProcessing.value = false;
		progressPercentage.value = 0;
		
		// 组装参数
		formData.value.conf = conf.value / 100;
		formData.value.username = userInfos.value.userName || 'default_user';
		formData.value.startTime = formatDate(new Date(), 'YYYY-MM-DD HH:mm:ss');
		
		// 构建视频流URL - 使用MJPEG流
		const queryParams = new URLSearchParams({
			username: formData.value.username,
			conf: formData.value.conf.toString(),
			startTime: formData.value.startTime
		}).toString();
		
		// 设置摄像头流URL（添加时间戳避免缓存）
		cameraStreamUrl.value = `http://${currentHost}:5000/predictCamera?${queryParams}&t=${Date.now()}`;
		
		ElMessage.success('摄像头检测已开启');
		cameraStatusMessage.value = '摄像头检测已启动，正在实时检测杂草...';
		cameraStatusType.value = 'success';
		
	} catch (error) {
		console.error('开启摄像头检测失败:', error);
		ElMessage.error('开启摄像头检测失败');
		cameraStatusMessage.value = '开启摄像头检测失败，请检查Flask服务';
		cameraStatusType.value = 'error';
		resetCameraState();
	}
};

// 关闭摄像头检测
const stopCamera = async () => {
	if (!isCameraActive.value) {
		ElMessage.warning('摄像头检测未运行');
		return;
	}
	
	try {
		isStopping.value = true;
		
		// 确认是否要停止
		await ElMessageBox.confirm(
			'确定要停止摄像头检测吗？',
			'确认',
			{
				confirmButtonText: '确定',
				cancelButtonText: '取消',
				type: 'warning',
			}
		);
		
		// 发送停止请求到Flask
		const response = await request.get('/flask/stopCamera');
		
		if (response.code === 0 || response.status === 200) {
			ElMessage.success('摄像头检测已停止');
			cameraStatusMessage.value = '摄像头检测已停止';
			cameraStatusType.value = 'info';
			
			// 延迟重置状态，确保Flask处理完成
			setTimeout(() => {
				resetCameraState();
			}, 1000);
			
		} else {
			ElMessage.error('停止摄像头检测失败');
			cameraStatusMessage.value = '停止摄像头检测失败，请重试';
			cameraStatusType.value = 'error';
			isStopping.value = false;
		}
		
	} catch (error) {
		// 用户取消操作
		if (error === 'cancel' || error === 'close') {
			isStopping.value = false;
			return;
		}
		
		console.error('停止摄像头检测异常:', error);
		ElMessage.error('停止摄像头检测异常');
		
		// 无论如何都重置状态
		setTimeout(() => {
			resetCameraState();
		}, 500);
	}
};

// 重置摄像头状态
const resetCameraState = () => {
	// 清除视频流URL
	cameraStreamUrl.value = '';
	
	// 重置状态
	isCameraActive.value = false;
	isStopping.value = false;
	isProcessing.value = false;
	progressPercentage.value = 0;
	
	// 强制释放img元素资源
	if (streamImgRef.value) {
		streamImgRef.value.src = '';
		streamImgRef.value.removeAttribute('src');
	}
	
	// 强制垃圾回收提示
	if (window.gc) {
		window.gc();
	}
};

// 处理视频流错误
const handleStreamError = (error: Event) => {
	console.error('摄像头流加载失败:', error);
	
	if (isCameraActive.value) {
		cameraStatusMessage.value = '摄像头流加载失败，可能Flask服务异常或摄像头被占用';
		cameraStatusType.value = 'error';
		
		// 自动重置状态
		setTimeout(() => {
			resetCameraState();
		}, 2000);
	}
};

// 监听视频流加载成功
const handleStreamLoad = () => {
	console.log('摄像头流加载成功');
	cameraStatusMessage.value = '摄像头流已连接，正在实时检测杂草';
	cameraStatusType.value = 'success';
};

// 【核心修复】页面激活时：完全重置状态
onActivated(() => {
	console.log('摄像头检测页面激活 - 重置所有状态');
	
	// 强制重置所有状态
	resetCameraState();
	
	// 重置表单
	formData.value = {
		username: '',
		conf: conf.value / 100,
		startTime: ''
	};
	
	// 清除状态消息
	cameraStatusMessage.value = '';
	
	// 重新获取用户信息
	if (stores && userInfos.value.userName) {
		formData.value.username = userInfos.value.userName;
	}
});

// 【核心修复】页面失活时：强制停止摄像头并清理资源
onDeactivated(() => {
	console.log('摄像头检测页面失活 - 强制清理');
	
	// 如果摄像头正在运行，强制停止
	if (isCameraActive.value) {
		console.log('检测到摄像头正在运行，强制停止...');
		
		// 发送停止请求（不等待响应）
		request.get('/flask/stopCamera').catch(() => {
			console.warn('停止摄像头请求失败，继续清理');
		});
		
		// 立即重置状态
		resetCameraState();
		
		ElMessage.info('摄像头检测已自动停止');
	}
	
	// 额外清理：强制清除可能的内存占用
	if (cameraStreamUrl.value) {
		cameraStreamUrl.value = '';
	}
	
	// 清除浏览器缓存中的图片
	if ('caches' in window) {
		caches.keys().then(cacheNames => {
			cacheNames.forEach(cacheName => {
				caches.delete(cacheName);
			});
		});
	}
});

// 页面卸载：最终清理
onUnmounted(() => {
	console.log('摄像头检测页面卸载 - 最终清理');
	resetCameraState();
});

// 页面挂载初始化
onMounted(() => {
  // 检查Flask服务是否可用
  checkFlaskConnection();
  
  // 原有逻辑
  state.form.conf = conf.value / 100;
  
  // 预加载用户信息
  if (stores && userInfos.value.userName) {
    formData.value.username = userInfos.value.userName;
  }
});

// 添加Flask连接检查方法
const checkFlaskConnection = async () => {
  try {
    const response = await request.get('/flask/test');
    console.log('Flask连接正常:', response);
  } catch (error) {
    console.error('Flask连接失败:', error);
    ElMessage.error('Flask服务未启动，请确保已启动Flask后端服务');
    cameraStatusMessage.value = 'Flask服务未启动，无法进行检测';
    cameraStatusType.value = 'error';
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
	justify-content: flex-start;
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
	padding: 20px;
	overflow: hidden;
	display: flex;
	justify-content: center;
	align-items: center;
	background: white;
	position: relative;
	min-height: 500px;
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);

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

.video-stream {
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

// 响应式适配
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
	
	.video-stream {
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
	
	.video-stream {
		max-height: 60vh;
	}
}
</style>
<template>
	<div class="system-predict-container layout-padding">
		<div class="system-predict-padding layout-padding-auto layout-padding-view">
			<div class="header">
				<div class="conf" style="display: flex; flex-direction: row; align-items: center;">
					<div
						style="font-size: 14px;margin-right: 20px;display: flex;justify-content: start;align-items: center;color: #909399;">
						设置最小置信度阈值
					</div>
					<el-slider v-model="conf" :format-tooltip="formatTooltip" style="width: 300px;" 
					  :min="0" :max="100" :step="1" />
				</div>
				<div class="button-section" style="margin-left: 20px">
					<el-button type="primary" @click="upData" class="predict-button" :disabled="state.isDetecting">
						{{ state.isDetecting ? '正在检测中' : '开始杂草检测' }}
					</el-button>
				</div>
			</div>
			<el-card shadow="hover" class="card">
				<!-- 核心修改：添加图片容器，支持检测框绘制 -->
				<div class="img-container" ref="imgContainer">
					<!-- 原图或检测结果图 -->
					<img 
						:src="currentImageUrl" 
						class="avatar" 
						alt="检测图片"
						ref="imageRef"
						@load="onImageLoad"
						v-show="currentImageUrl"
					/>
					<!-- 检测框画布 -->
					<canvas 
						ref="canvasRef" 
						class="detection-canvas"
						v-show="currentImageUrl"
					></canvas>
					
					<!-- 上传区域（没有图片时显示） -->
					<el-upload 
						v-if="!currentImageUrl"
						v-model="state.img" 
						ref="uploadFile" 
						class="avatar-uploader"
						:action="uploadAction" 
						:show-file-list="false" 
						:on-success="handleAvatarSuccessone"
						:before-upload="beforeUpload"
					>
						<el-icon class="avatar-uploader-icon">
							<Plus />
						</el-icon>
					</el-upload>
				</div>
			</el-card>
			
			<!-- 检测结果信息 -->
			<el-card class="result-section" v-if="state.predictionResult.label || detections.length > 0">
				<div class="bottom">
					<div style="width: 33%">识别结果：{{ state.predictionResult.label || '未识别' }}</div>
					<div style="width: 33%">预测概率：{{ state.predictionResult.confidence || '0%' }}</div>
					<div style="width: 33%">总时间：{{ state.predictionResult.allTime || '0秒' }}</div>
				</div>
				
				<!-- 检测框详细信息 -->
				<div class="detections-detail" v-if="detections.length > 0">
					<div class="detection-count" style="margin-top: 15px; font-weight: bold;">
						共检测到 {{ detections.length }} 个目标：
					</div>
					<el-table :data="detections" style="width: 100%; margin-top: 10px;" size="small">
						<el-table-column prop="weed_name" label="杂草名称" width="120"></el-table-column>
						<el-table-column prop="confidence" label="置信度" width="100">
							<template #default="{ row }">
								{{ (row.confidence * 100).toFixed(2) }}%
							</template>
						</el-table-column>
						<el-table-column prop="bbox" label="位置" width="200">
							<template #default="{ row }">
								({{ row.bbox.x }}, {{ row.bbox.y }}) - 
								宽:{{ row.bbox.width }}px, 高:{{ row.bbox.height }}px
							</template>
						</el-table-column>
						<el-table-column label="操作" width="100">
							<template #default="{ row, $index }">
								<el-button 
									size="small" 
									@click="highlightDetection($index)"
									:type="highlightedIndex === $index ? 'primary' : 'default'"
								>
									{{ highlightedIndex === $index ? '已高亮' : '高亮' }}
								</el-button>
							</template>
						</el-table-column>
					</el-table>
				</div>
			</el-card>
		</div>
	</div>
</template>

<script setup lang="ts" name="imgPredict">
import { reactive, ref, onMounted, onActivated, onDeactivated, computed, nextTick, onUnmounted } from 'vue';
import type { UploadInstance, UploadProps } from 'element-plus';
import { ElMessage } from 'element-plus';
import request from '/@/utils/request';
import { Plus } from '@element-plus/icons-vue';
import { useUserInfo } from '/@/stores/userInfo';
import { storeToRefs } from 'pinia';
import { formatDate } from '/@/utils/formatTime';

// 核心变量：分离原图和检测结果图
const imageUrl = ref(''); // 上传的原图临时地址
const detectedImageUrl = ref(''); // 后端返回的带检测框图片地址（相对路径，走代理）
const conf = ref(50); // 置信度默认50%
const uploadFile = ref<UploadInstance>();
const stores = useUserInfo();
const { userInfos } = storeToRefs(stores);

// 新增：检测框相关变量
const imageRef = ref<HTMLImageElement | null>(null);
const canvasRef = ref<HTMLCanvasElement | null>(null);
const imgContainer = ref<HTMLElement | null>(null);
const detections = ref<any[]>([]); // 存储检测框数据
const highlightedIndex = ref<number | null>(null); // 当前高亮的检测框索引

// 计算当前显示的图片URL（直接使用相对路径，Vite代理自动转发）
const currentImageUrl = computed(() => {
	return detectedImageUrl.value || imageUrl.value;
});

// 上传地址：走Vite代理/flask（和vite.config.ts的/flask代理匹配，后端上传接口是/flask/upload）
const uploadAction = ref('/flask/upload');

const state = reactive({
	img: '', // 上传图片的后端标识
	predictionResult: { label: '', confidence: '', allTime: '' },
	form: { username: '', inputImg: null, conf: null, startTime: '' },
	isDetecting: false, // 检测状态锁，防止重复请求
});

// 置信度滑块格式化
const formatTooltip = (val: number) => val / 100;

// 上传前验证
const beforeUpload = (file: File) => {
	// 检查文件类型
	const isImage = file.type.startsWith('image/');
	if (!isImage) {
		ElMessage.error('只能上传图片文件！');
		return false;
	}
	
	// 检查文件大小（限制5MB）
	const isLt5M = file.size / 1024 / 1024 < 5;
	if (!isLt5M) {
		ElMessage.error('图片大小不能超过5MB！');
		return false;
	}
	
	return true;
};

// 图片上传成功回调
const handleAvatarSuccessone: UploadProps['onSuccess'] = (response, uploadFile) => {
	// 上传新图时，清空之前的检测结果和带框图
	clearCanvas(); // 清理画布
	detectedImageUrl.value = '';
	detections.value = [];
	highlightedIndex.value = null;
	state.predictionResult = { label: '', confidence: '', allTime: '' };
	
	// 释放旧的图片URL（避免内存泄漏）
	if (imageUrl.value && imageUrl.value.startsWith('blob:')) {
		URL.revokeObjectURL(imageUrl.value);
	}
	
	// 生成原图临时预览地址（本地blob，无需代理）
	imageUrl.value = URL.createObjectURL(uploadFile.raw!);
	// 适配后端上传响应格式，获取图片标识
	state.img = response.data || response.fileName || '';
	ElMessage.success('杂草检测图片上传成功！');
};

// 清理画布
const clearCanvas = () => {
	if (canvasRef.value) {
		const canvas = canvasRef.value;
		const ctx = canvas.getContext('2d');
		if (ctx) {
			ctx.clearRect(0, 0, canvas.width, canvas.height);
		}
	}
};

// 图片加载完成事件
const onImageLoad = () => {
	nextTick(() => {
		// 等待DOM更新后绘制检测框
		drawDetections();
	});
};

// 绘制检测框（原有逻辑不变，保留所有绘制功能）
const drawDetections = () => {
	if (!canvasRef.value || !imageRef.value || detections.value.length === 0) {
		return;
	}
	
	const canvas = canvasRef.value;
	const ctx = canvas.getContext('2d');
	const img = imageRef.value;
	
	if (!ctx) return;
	
	// 设置canvas尺寸与图片一致
	canvas.width = img.width;
	canvas.height = img.height;
	
	// 清空画布
	ctx.clearRect(0, 0, canvas.width, canvas.height);
	
	// 绘制每个检测框
	detections.value.forEach((det, index) => {
		const bbox = det.bbox;
		
		// 获取坐标（支持两种格式）
		let x, y, width, height;
		
		if (bbox.x !== undefined && bbox.y !== undefined && bbox.width !== undefined && bbox.height !== undefined) {
			// 格式1: {x, y, width, height}
			x = bbox.x;
			y = bbox.y;
			width = bbox.width;
			height = bbox.height;
		} else if (bbox.x1 !== undefined && bbox.y1 !== undefined && bbox.x2 !== undefined && bbox.y2 !== undefined) {
			// 格式2: {x1, y1, x2, y2}
			x = bbox.x1;
			y = bbox.y1;
			width = bbox.x2 - bbox.x1;
			height = bbox.y2 - bbox.y1;
		} else {
			// 坐标格式不支持
			console.warn('不支持的bbox格式:', bbox);
			return;
		}
		
		// 判断是否高亮
		const isHighlighted = highlightedIndex.value === index;
		
		// 设置绘制样式
		ctx.strokeStyle = isHighlighted ? '#ff0000' : '#00ff00'; // 高亮红色，普通绿色
		ctx.lineWidth = isHighlighted ? 3 : 2;
		ctx.fillStyle = isHighlighted ? 'rgba(255, 0, 0, 0.2)' : 'rgba(0, 255, 0, 0.1)';
		
		// 绘制矩形框
		ctx.strokeRect(x, y, width, height);
		ctx.fillRect(x, y, width, height);
		
		// 绘制标签背景
		ctx.fillStyle = isHighlighted ? '#ff0000' : '#00ff00';
		ctx.font = '14px Arial';
		const text = `${det.weed_name} ${(det.confidence * 100).toFixed(1)}%`;
		const textWidth = ctx.measureText(text).width;
		
		// 标签背景位置（避免超出图片边界）
		const labelX = Math.max(0, Math.min(x, canvas.width - textWidth - 10));
		const labelY = Math.max(20, y);
		
		ctx.fillRect(labelX, labelY - 20, textWidth + 10, 20);
		
		// 绘制文字
		ctx.fillStyle = '#ffffff';
		ctx.fillText(text, labelX + 5, labelY - 5);
		
		// 绘制角标（可选）
		ctx.strokeStyle = isHighlighted ? '#ff0000' : '#00ff00';
		ctx.lineWidth = 2;
		
		// 左上角
		const cornerSize = 15;
		ctx.beginPath();
		ctx.moveTo(x, y + cornerSize);
		ctx.lineTo(x, y);
		ctx.lineTo(x + cornerSize, y);
		ctx.stroke();
		
		// 右上角
		ctx.beginPath();
		ctx.moveTo(x + width - cornerSize, y);
		ctx.lineTo(x + width, y);
		ctx.lineTo(x + width, y + cornerSize);
		ctx.stroke();
		
		// 左下角
		ctx.beginPath();
		ctx.moveTo(x, y + height - cornerSize);
		ctx.lineTo(x, y + height);
		ctx.lineTo(x + cornerSize, y + height);
		ctx.stroke();
		
		// 右下角
		ctx.beginPath();
		ctx.moveTo(x + width - cornerSize, y + height);
		ctx.lineTo(x + width, y + height);
		ctx.lineTo(x + width, y + height - cornerSize);
		ctx.stroke();
	});
};

// 高亮指定检测框（原有逻辑不变）
const highlightDetection = (index: number) => {
	if (highlightedIndex.value === index) {
		highlightedIndex.value = null; // 取消高亮
	} else {
		highlightedIndex.value = index; // 设置高亮
	}
	
	// 重新绘制检测框
	drawDetections();
};

// 开始杂草检测
const upData = async () => {
	// 多重校验：防重复请求、防无图、防非法置信度
	if (state.isDetecting) return ElMessage.warning('正在检测中，请勿重复点击！');
	if (!state.img) return ElMessage.warning('请先上传杂草检测图片！');
	if (isNaN(Number(conf.value)) || conf.value < 0 || conf.value > 100) return ElMessage.warning('请设置0-100的有效置信度！');

	// 组装参数：修复类型为Number，适配后端接收
	state.isDetecting = true;
	state.form.conf = conf.value / 100; // 直接传Number，无需转字符串
	state.form.username = userInfos.value.userName || 'default_user';
	state.form.inputImg = state.img;
	state.form.startTime = formatDate(new Date(), 'YYYY-MM-DD HH:mm:ss'); // 修复时间格式符

	try {
		// 🔥 核心修改1：检测接口改为/predict，匹配后端main.py和vite代理配置
		const res = await request.post('/predict', state.form);
		let result = res.data || res;
		result = typeof result === 'string' ? JSON.parse(result) : result;

		if (result.status === 200 || result.code === 0) {
			// 处理检测结果，兼容后端两种响应码（200/0）
			let label = result.label || '未识别到杂草';
			label = Array.isArray(label) ? label.join('、') : label;
			const confidence = result.confidence ? `${(Number(result.confidence) * 100).toFixed(2)}%` : '0%';
			const allTime = result.allTime ? `${Number(result.allTime).toFixed(2)}秒` : '0秒';

			// 更新页面：渲染带检测框的图片
			state.predictionResult = { label, confidence, allTime };
			
			// 存储检测框数据
			if (result.detections && Array.isArray(result.detections)) {
				detections.value = result.detections;
				highlightedIndex.value = null;
			} else {
				detections.value = [];
			}
			
			// 渲染后端返回的带检测框图片
			if (result.outImg) {
				detectedImageUrl.value = result.outImg; // 直接赋值相对路径，代理自动转发
				
				// 等待图片加载完成后绘制检测框
				nextTick(() => {
					if (imageRef.value) {
						// 移除之前的load事件监听器，避免重复绑定
						imageRef.value.onload = null;
						imageRef.value.onload = () => {
							drawDetections();
						};
					}
				});
			} else {
				// 如果没有检测后图片，使用原图并绘制检测框
				detectedImageUrl.value = '';
				if (imageRef.value) {
					imageRef.value.onload = () => {
						drawDetections();
					};
				}
			}
			
			// 检测成功提示，兼容后端detection_count字段
			ElMessage.success(`杂草检测成功！共检测到 ${result.detection_count || detections.value.length} 个目标`);
		} else {
			ElMessage.error(result.message || result.msg || '杂草检测失败，请重试');
		}
	} catch (error) {
		console.error('检测接口请求失败:', error);
		// 错误提示适配代理配置
		ElMessage.error('检测接口调用失败！请检查Flask是否启动+接口路径是否正确！');
	} finally {
		// 无论成功失败，释放检测锁
		state.isDetecting = false;
	}
};

// 彻底清理所有资源（原有逻辑不变）
const cleanupAllResources = () => {
	// 1. 释放图片URL（避免内存泄漏）
	if (imageUrl.value && imageUrl.value.startsWith('blob:')) {
		URL.revokeObjectURL(imageUrl.value);
	}
	
	// 2. 清除远程图片URL（避免缓存）
	if (detectedImageUrl.value) {
		// 强制浏览器清理图片缓存
		const img = new Image();
		img.src = detectedImageUrl.value + '?t=' + Date.now();
		setTimeout(() => {
			img.src = '';
		}, 100);
	}
	
	// 3. 清理画布
	clearCanvas();
	
	// 4. 重置所有状态
	imageUrl.value = '';
	detectedImageUrl.value = '';
	detections.value = [];
	highlightedIndex.value = null;
	state.img = '';
	state.isDetecting = false;
	state.predictionResult = { label: '', confidence: '', allTime: '' };
	
	// 5. 清除上传组件
	if (uploadFile.value) {
		uploadFile.value.clearFiles();
	}
	
	// 6. 清理图片元素引用
	if (imageRef.value) {
		imageRef.value.src = '';
		imageRef.value.removeAttribute('src');
	}
	
	// 7. 清理canvas引用
	if (canvasRef.value) {
		const canvas = canvasRef.value;
		canvas.width = 0;
		canvas.height = 0;
	}
	
	console.log('图片检测页面资源已彻底清理');
};

// 页面激活时：重置状态，重新初始化（原有逻辑不变）
onActivated(() => {
	console.log('图片检测页面激活 - 重置状态');
	
	// 重置检测状态和结果，防止路由切换后状态残留
	state.isDetecting = false;
	state.predictionResult = { label: '', confidence: '', allTime: '' };
	detections.value = [];
	highlightedIndex.value = null;
	
	// 重置上传组件（清空未完成的上传）
	if (uploadFile.value) uploadFile.value.clearFiles();
	
	// 重新绘制检测框（如果有）
	if (detections.value.length > 0) {
		drawDetections();
	}
});

// 页面失活时：彻底清理所有资源（原有逻辑不变）
onDeactivated(() => {
	console.log('图片检测页面失活 - 彻底清理资源');
	cleanupAllResources();
});

// Flask连通性检测
const checkFlaskConnection = async () => {
  try {
    // 🔥 核心修改2：连通性检测接口改为/predict，匹配后端和vite代理
    const response = await fetch('/predict', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({})
    });
    if (response.ok) {
      console.log('Flask服务正常（代理转发成功）');
      // 直接定位页面顶部的提示元素（根据页面结构）
      const tipElement = document.querySelector('.system-predict-container .NOT-FOUND');
      if (tipElement) {
        tipElement.style.display = 'none'; // 强制隐藏
      }
    }
  } catch (error) {
    ElMessage.warning('Flask服务未启动或代理配置错误！');
  }
};

// 页面挂载初始化（原有逻辑不变，仅适配代理）
onMounted(() => {
  // 优先检查Flask服务（走代理）
  checkFlaskConnection();
  
  // 原有逻辑
  state.form.conf = conf.value / 100;
  
  // 监听窗口大小变化，重新绘制检测框
  window.addEventListener('resize', drawDetections);
  
  // 确保页面加载时清理旧状态
  cleanupAllResources();
  
  // 预加载用户信息
  if (stores && userInfos.value.userName) {
    state.form.username = userInfos.value.userName;
  }
});

// 组件卸载前清理（原有逻辑不变）
onUnmounted(() => {
	window.removeEventListener('resize', drawDetections);
	cleanupAllResources();
});
</script>

<style scoped lang="scss">
.system-predict-container {
	width: 100%;
	height: 100vh;
	display: flex;
	flex-direction: column;

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
	padding-bottom: 10px;
	border-bottom: 1px solid #e5e7eb;
	margin-bottom: 15px;
}

.card {
	width: 100%;
	flex: 1;
	border-radius: 10px;
	margin-top: 0;
	display: flex;
	justify-content: center;
	align-items: center;
	padding: 20px;
	background: radial-gradient(circle, #d3e3f1 0%, #ffffff 100%);
}

// 图片容器
.img-container {
	position: relative;
	width: 100%;
	height: 100%;
	display: flex;
	justify-content: center;
	align-items: center;
}

.avatar-uploader {
	width: 100%;
	height: 100%;
}

.avatar {
	width: 100%;
	max-height: 70vh;
	height: auto;
	display: block;
	object-fit: contain;
	border-radius: 6px;
	box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}

// 检测框画布
.detection-canvas {
	position: absolute;
	top: 0;
	left: 0;
	width: 100%;
	height: 100%;
	pointer-events: none; /* 允许点击穿透到图片 */
}

.el-icon.avatar-uploader-icon {
	font-size: 28px;
	color: #8c939d;
	width: 100%;
	height: 600px;
	text-align: center;
	line-height: 600px;
}

.button-section {
	display: flex;
	justify-content: center;
	min-width: 200px;
}

.predict-button {
	width: 100%;
}

.result-section {
	width: 100%;
	margin-top: 15px;
	text-align: center;
	border-radius: 6px;
	padding: 20px 0;
	background: radial-gradient(circle, #d3e3f1 0%, #ffffff 100%);
}

.bottom {
	width: 100%;
	font-size: 18px;
	display: flex;
	flex-direction: row;
	justify-content: center;
	align-items: center;
	gap: 40px;
	flex-wrap: wrap;
}

// 检测框详情区域
.detections-detail {
	margin-top: 15px;
	padding: 0 20px;
	
	.detection-count {
		font-size: 16px;
		color: #409eff;
		text-align: left;
		margin-bottom: 10px;
	}
	
	:deep(.el-table) {
		.el-table__row:hover {
			background-color: #f5f7fa;
			cursor: pointer;
		}
	}
}

// 响应式适配
@media (max-width: 1000px) {
	.header {
		gap: 10px;
	}
	.button-section {
		margin-left: 0 !important;
		width: 100%;
		min-width: unset;
	}
	.bottom {
		gap: 20px;
	}
	.bottom > div {
		width: 100% !important;
		margin: 5px 0;
	}
	
	.detections-detail {
		padding: 0 10px;
	}
}
</style>
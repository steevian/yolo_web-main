<template>
	<div class="system-role-container layout-padding">
		<div class="system-role-padding layout-padding-auto layout-padding-view workbench-page-body">
			<div class="workbench-title-row">
				<div>
					<h3 class="workbench-title">数据集分析</h3>
					<p class="workbench-subtitle">查看杂草训练数据集的样本规模、类别分布与图像尺寸统计。</p>
				</div>
			</div>

			<el-card class="mb15">
				<el-form inline>
					<el-form-item label="数据集">
						<el-select v-model="currentDataset" style="width: 260px" filterable placeholder="请选择数据集">
							<el-option v-for="item in datasets" :key="item.name" :label="item.name" :value="item.name" />
						</el-select>
					</el-form-item>
					<el-form-item>
						<el-button type="primary" @click="loadAnalysis">分析</el-button>
					</el-form-item>
				</el-form>
			</el-card>

			<div class="analysis-cards mb15">
				<el-card>
					<div class="metric-title">训练集图片</div>
					<div class="metric-value">{{ analysis.trainImages || 0 }}</div>
				</el-card>
				<el-card>
					<div class="metric-title">验证集图片</div>
					<div class="metric-value">{{ analysis.valImages || 0 }}</div>
				</el-card>
				<el-card>
					<div class="metric-title">类别数量</div>
					<div class="metric-value">{{ classRows.length }}</div>
				</el-card>
			</div>

			<el-row :gutter="12">
				<el-col :span="12">
					<el-card>
						<template #header>类别分布</template>
						<el-table :data="classRows" v-loading="loading" style="width: 100%">
							<el-table-column prop="className" label="类别" min-width="160" />
							<el-table-column prop="count" label="标注数量" min-width="120" />
						</el-table>
					</el-card>
				</el-col>
				<el-col :span="12">
					<el-card>
						<template #header>图像尺寸样本</template>
						<el-table :data="sizeRows" v-loading="loading" style="width: 100%">
							<el-table-column prop="width" label="宽" min-width="100" />
							<el-table-column prop="height" label="高" min-width="100" />
						</el-table>
					</el-card>
				</el-col>
			</el-row>
		</div>
	</div>
</template>

<script setup lang="ts" name="trainDatasetAnalysisPage">
import { computed, onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { useTrainApi } from '@/api/train';

const trainApi = useTrainApi();
const loading = ref(false);
const datasets = ref<any[]>([]);
const currentDataset = ref('');
const analysis = ref<Record<string, any>>({});

const classRows = computed(() => {
	const distribution = analysis.value.classDistribution || {};
	return Object.keys(distribution).map((key) => ({ className: key, count: distribution[key] }));
});

const sizeRows = computed(() => {
	const rows = analysis.value.imageSizes || [];
	return rows.map((item: number[]) => ({ width: item[0], height: item[1] }));
});

const loadDatasets = async () => {
	try {
		const res = await trainApi.getTrainDatasets();
		datasets.value = res?.data?.datasets || [];
		if (!currentDataset.value && datasets.value.length > 0) {
			currentDataset.value = datasets.value[0].name;
		}
	} catch (error) {
		ElMessage.error('获取数据集列表失败');
	}
};

const loadAnalysis = async () => {
	if (!currentDataset.value) {
		ElMessage.warning('请先选择数据集');
		return;
	}
	loading.value = true;
	try {
		const res = await trainApi.getTrainDatasetAnalysis(currentDataset.value);
		analysis.value = res?.data || {};
	} catch (error) {
		ElMessage.error('加载数据集分析失败');
	} finally {
		loading.value = false;
	}
};

onMounted(async () => {
	await loadDatasets();
	await loadAnalysis();
});
</script>

<style scoped lang="scss">
.analysis-cards {
	display: grid;
	grid-template-columns: repeat(3, minmax(0, 1fr));
	gap: 12px;
}

.metric-title {
	font-size: 12px;
	color: #909399;
}

.metric-value {
	margin-top: 8px;
	font-size: 22px;
	font-weight: 600;
	color: #303133;
}

@media (max-width: 1200px) {
	.analysis-cards {
		grid-template-columns: repeat(1, minmax(0, 1fr));
	}
}
</style>

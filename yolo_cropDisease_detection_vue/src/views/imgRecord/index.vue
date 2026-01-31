<template>
	<div class="system-role-container layout-padding">
		<div class="system-role-padding layout-padding-auto layout-padding-view">
			<div class="system-user-search mb15">
				<el-input v-model="state.tableData.param.search1" size="default" placeholder="请输入用户名"
					style="max-width: 180px"> </el-input>
				<el-input v-model="state.tableData.param.search2" size="default" placeholder="请输入识别结果"
					style="max-width: 180px; margin-left: 15px">
				</el-input>
				<el-button size="default" type="primary" class="ml10" @click="getTableData()">
					<el-icon>
						<ele-Search />
					</el-icon>
					查询
				</el-button>
			</div>
			<el-table :data="state.tableData.data" style="width: 100%">
				<el-table-column type="expand">
					<template #default="props">
						<div m="4">
							<p style="margin-left: 20px; font-size: 16px; font-weight: 800;">详细识别结果：</p>
							<el-table :data="props.row.family">
								<el-table-column prop="label" label="识别结果" align="center" />
								<el-table-column prop="confidence" label="置信度" show-overflow-tooltip
									align="center">
									<template #default="{ row }">
										{{ (row.confidence * 100).toFixed(2) }}%
									</template>
								</el-table-column>
								<el-table-column prop="startTime" label="识别时间" align="center" />
							</el-table>
						</div>
					</template>
				</el-table-column>
				<el-table-column prop="num" label="序号" width="80" align="center" />
				<el-table-column prop="input_img" label="原始图片" width="120" align="center">
					<template #default="scope">
						<img :src="scope.row.input_img" width="120" height="80" style="object-fit: cover;" />
					</template>
				</el-table-column>
				<el-table-column prop="out_img" label="预测图片" width="120" align="center">
					<template #default="scope">
						<img :src="scope.row.out_img" width="120" height="80" style="object-fit: cover;" v-if="scope.row.out_img" />
						<span v-else>无结果图</span>
					</template>
				</el-table-column>
				<el-table-column prop="confidence" label="置信度" show-overflow-tooltip align="center">
					<template #default="{ row }">
						{{ (row.confidence * 100).toFixed(2) }}%
					</template>
				</el-table-column>
				<el-table-column prop="conf" label="最小阈值" show-overflow-tooltip align="center">
					<template #default="{ row }">
						{{ (row.conf * 100).toFixed(0) }}%
					</template>
				</el-table-column>
				<el-table-column prop="all_time" label="总用时" show-overflow-tooltip align="center">
					<template #default="{ row }">
						{{ row.all_time }}秒
					</template>
				</el-table-column>
				<el-table-column prop="start_time" label="识别时间" width="200" align="center" />
				<el-table-column prop="username" label="识别用户" show-overflow-tooltip align="center"></el-table-column>
				<el-table-column label="操作" width="80">
					<template #default="scope">
						<el-button size="small" text type="primary" @click="onRowDel(scope.row)">删除</el-button>
					</template>
				</el-table-column>
			</el-table>
			<el-pagination @size-change="onHandleSizeChange" @current-change="onHandleCurrentChange" class="mt15"
				:pager-count="5" :page-sizes="[10, 20, 30]" v-model:current-page="state.tableData.param.pageNum"
				background v-model:page-size="state.tableData.param.pageSize"
				:layout="state.tableData.total > 0 ? 'total, sizes, prev, pager, next, jumper' : ''" 
				:total="state.tableData.total"
				:hide-on-single-page="state.tableData.total <= state.tableData.param.pageSize">
			</el-pagination>
			
			<!-- 空数据提示 -->
			<el-empty v-if="state.tableData.data.length === 0" description="暂无检测记录" :image-size="200">
				<template #image>
					<el-icon size="100" color="#c0c4cc">
						<ele-Picture />
					</el-icon>
				</template>
			</el-empty>
		</div>
	</div>
</template>

<script setup lang="ts" name="systemRole">
import { reactive, onMounted, watch } from 'vue';
import { ElMessageBox, ElMessage } from 'element-plus';
import { Picture } from '@element-plus/icons-vue';
import request from '/@/utils/request';
import { useUserInfo } from '/@/stores/userInfo';
import { storeToRefs } from 'pinia';

const stores = useUserInfo();
const { userInfos } = storeToRefs(stores);

const state = reactive({
	tableData: {
		data: [] as any[],
		total: 0,
		loading: false,
		param: {
			search1: '', // 用户名搜索
			search2: '', // 标签搜索
			pageNum: 1,
			pageSize: 10,
		},
	},
});

// 获取表格数据
const getTableData = () => {
	state.tableData.loading = true;
	
	// 构建查询参数
	const params: any = {
		page: state.tableData.param.pageNum,
		page_size: state.tableData.param.pageSize,
	};
	
	// 添加搜索条件
	if (state.tableData.param.search1) {
		params.username = state.tableData.param.search1;
	}
	if (state.tableData.param.search2) {
		params.search_label = state.tableData.param.search2;
	}
	
	// 如果不是管理员，只显示当前用户的记录
	if (userInfos.value.userName !== 'admin') {
		params.username = userInfos.value.userName;
	}
	
	console.log('查询参数:', params);
	
	// 请求Flask服务的图片记录接口
	request.get('/flask/img_records', { params })
		.then((res) => {
			console.log('获取记录响应:', res);
			
			if (res.status === 200 || res.code === 200) {
				const data = res.data || res;
				
				state.tableData.data = [];
				state.tableData.total = data.total || 0;
				
				// 处理每一条记录
				if (data.records && Array.isArray(data.records)) {
					data.records.forEach((record: any, index: number) => {
						// 解析detections字段
						let detections = [];
						try {
							if (record.detections) {
								detections = typeof record.detections === 'string' 
									? JSON.parse(record.detections) 
									: record.detections;
							}
						} catch (error) {
							console.error('解析detections失败:', error);
						}
						
						// 解析label字段
						let labels = [];
						try {
							if (record.label) {
								labels = typeof record.label === 'string'
									? JSON.parse(record.label)
									: record.label;
							}
						} catch (error) {
							console.error('解析label失败:', error);
							labels = record.label ? [record.label] : [];
						}
						
						// 解析confidence字段
						let confidences = [];
						try {
							if (record.confidence) {
								confidences = typeof record.confidence === 'string'
									? JSON.parse(record.confidence)
									: [record.confidence];
							}
						} catch (error) {
							console.error('解析confidence失败:', error);
							confidences = record.confidence ? [record.confidence] : [];
						}
						
						// 构建family数据
						const family = labels.map((label: string, idx: number) => ({
							label: label,
							confidence: confidences[idx] || 0,
							startTime: record.start_time || record.startTime
						}));
						
						// 构建表格行数据
						const transformedData = {
							id: record.id,
							num: (state.tableData.param.pageNum - 1) * state.tableData.param.pageSize + index + 1,
							input_img: record.input_img || record.inputImg,
							out_img: record.out_img || record.outImg,
							confidence: record.confidence || 0,
							all_time: record.all_time || record.allTime,
							conf: record.conf || 0.5,
							start_time: record.start_time || record.startTime,
							username: record.username,
							label: record.label || '',
							family: family,
							detections: detections
						};
						
						state.tableData.data.push(transformedData);
					});
				}
				
				ElMessage.success(`获取到 ${state.tableData.data.length} 条记录`);
			} else {
				ElMessage.error(data.message || '获取记录失败');
			}
		})
		.catch((error) => {
			console.error('获取记录失败:', error);
			ElMessage.error('获取记录失败，请检查Flask服务');
		})
		.finally(() => {
			state.tableData.loading = false;
		});
};

// 删除记录
const onRowDel = (row: any) => {
	ElMessageBox.confirm(`此操作将永久删除该检测记录，是否继续?`, '提示', {
		confirmButtonText: '确认',
		cancelButtonText: '取消',
		type: 'warning',
	})
		.then(() => {
			console.log('删除记录:', row);
			
			request.delete(`/flask/img_records/${row.id}`)
				.then((res) => {
					console.log('删除响应:', res);
					
					if (res.code === 200 || res.status === 200) {
						ElMessage.success('删除成功！');
						
						// 重新获取数据
						setTimeout(() => {
							getTableData();
						}, 500);
					} else {
						ElMessage.error(res.message || '删除失败');
					}
				})
				.catch((error) => {
					console.error('删除失败:', error);
					ElMessage.error('删除失败，请检查Flask服务');
				});
		})
		.catch(() => { });
};

// 分页大小改变
const onHandleSizeChange = (val: number) => {
	state.tableData.param.pageSize = val;
	state.tableData.param.pageNum = 1; // 重置到第一页
	getTableData();
};

// 分页页码改变
const onHandleCurrentChange = (val: number) => {
	state.tableData.param.pageNum = val;
	getTableData();
};

// 监听搜索条件变化，自动搜索
watch(
	() => [state.tableData.param.search1, state.tableData.param.search2],
	() => {
		// 防抖处理，避免频繁请求
		clearTimeout((window as any).searchTimer);
		(window as any).searchTimer = setTimeout(() => {
			state.tableData.param.pageNum = 1; // 搜索时回到第一页
			getTableData();
		}, 500);
	}
);

// 页面加载时
onMounted(() => {
	getTableData();
});
</script>

<style scoped lang="scss">
.system-role-container {
	width: 100%;
	height: 100vh;
	display: flex;
	flex-direction: column;

	.system-role-padding {
		padding: 15px;
		height: 100%;
		display: flex;
		flex-direction: column;
	}
}

.system-user-search {
	display: flex;
	align-items: center;
	flex-wrap: wrap;
	gap: 10px;
	padding: 15px;
	background: white;
	border-radius: 8px;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	margin-bottom: 20px;
	
	.el-input {
		flex: 1;
		min-width: 200px;
	}
}

.mb15 {
	margin-bottom: 15px;
}

.ml10 {
	margin-left: 10px;
}

.mt15 {
	margin-top: 15px;
}

.el-table {
	flex: 1;
	background: white;
	border-radius: 8px;
	overflow: hidden;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	
	:deep(.el-table__row) {
		&:hover {
			background-color: #f5f7fa;
		}
	}
	
	:deep(img) {
		border-radius: 4px;
		transition: transform 0.3s ease;
		
		&:hover {
			transform: scale(1.05);
			cursor: pointer;
		}
	}
}

// 响应式适配
@media (max-width: 768px) {
	.system-user-search {
		flex-direction: column;
		align-items: stretch;
		
		.el-input {
			width: 100%;
			min-width: unset;
			margin-bottom: 10px;
			
			&:last-child {
				margin-bottom: 0;
			}
		}
		
		.el-button {
			width: 100%;
			margin-left: 0 !important;
		}
	}
	
	.el-table {
		:deep(.el-table__cell) {
			padding: 8px 0;
		}
	}
}
</style>
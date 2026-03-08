import request from '@/utils/request';

export interface TrainTaskPayload {
	taskName: string;
	modelType: string;
	datasetName: string;
	epochs: number;
	batchSize: number;
	imageSize: number;
	remark?: string;
}

export function useTrainApi() {
	return {
		getTrainTasks: (params?: Record<string, any>) => {
			return request({
				url: '/flask/train/tasks',
				method: 'get',
				params,
			});
		},
		createTrainTask: (data: TrainTaskPayload) => {
			return request({
				url: '/flask/train/tasks',
				method: 'post',
				data,
			});
		},
		getTrainMonitor: (params?: Record<string, any>) => {
			return request({
				url: '/flask/train/monitor',
				method: 'get',
				params,
			});
		},
		getTrainDatasets: () => {
			return request({
				url: '/flask/train/datasets',
				method: 'get',
			});
		},
		getTrainDatasetAnalysis: (datasetName: string) => {
			return request({
				url: `/flask/train/datasets/${encodeURIComponent(datasetName)}/analysis`,
				method: 'get',
			});
		},
		getTrainModelCompare: (params?: Record<string, any>) => {
			return request({
				url: '/flask/train/models/compare',
				method: 'get',
				params,
			});
		},
	};
}

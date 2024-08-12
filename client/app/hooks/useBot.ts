import {
  createBot,
  deleteBot,
  getBotConfig,
  getBotDetail,
  getBotInfoByRepoName,
  getBotList,
  getChunkList,
  updateBot,
} from '@/app/services/BotsController';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

export const useBotDetail = (id: string) => {
  return useQuery({
    queryKey: [`bot.detail.${id}`, id],
    queryFn: async () => getBotDetail(id),
    select: (data) => data?.[0],
    enabled: !!id,
    retry: false,
  });
};

export const useBotConfig = (id: string, enabled: boolean) => {
  return useQuery({
    queryKey: [`bot.config.${id}`, id],
    queryFn: async () => getBotConfig(id),
    select: (data) => data?.[0],
    enabled,
    retry: false,
  });
};

export const useBotList = (
  personal: boolean = false,
  name: string = '',
  enabled: boolean = true,
) => {
  return useQuery({
    queryKey: [`bot.list.${personal}`, name],
    queryFn: async () => getBotList(personal, name),
    enabled,
    retry: false,
  });
};

export function useBotDelete() {
  const mutation = useMutation({
    mutationFn: deleteBot,
  });

  return {
    deleteBot: mutation.mutate,
    isLoading: mutation.isPending,
    error: mutation.error,
    isSuccess: mutation.isSuccess,
  };
}

export function useBotEdit() {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: updateBot,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['bot.list.false'],
        refetchType: 'active',
      });
    },
  });

  return {
    updateBot: mutation.mutate,
    isLoading: mutation.isPending,
    error: mutation.error,
    isSuccess: mutation.isSuccess,
  };
}

export function useBotCreate() {
  const mutation = useMutation({
    mutationFn: createBot,
  });

  return {
    data: mutation.data?.data?.data,
    createBot: mutation.mutate,
    isLoading: mutation.isPending,
    error: mutation.error,
    isSuccess: mutation.isSuccess,
  };
}

export function useBotConfigGenerator() {
  const mutation = useMutation({
    mutationFn: getBotInfoByRepoName,
  });
  return {
    data: mutation.data?.data?.data,
    getBotInfoByRepoName: mutation.mutate,
    isLoading: mutation.isPending,
    error: mutation.error,
    isSuccess: mutation.isSuccess,
  };
}

export const useBotRAGChunkList = (
  botId: string,
  page_size: number,
  page_number: number,
  enabled: boolean = true,
) => {
  return useQuery({
    queryKey: [`rag.chunk.list`, botId],
    queryFn: async () => getChunkList(botId, page_size, page_number),
    select: (data) => data,
    enabled,
    retry: true,
  });
};

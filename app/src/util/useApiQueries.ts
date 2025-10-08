// import { useWeb3Account, useWeb3ChainId } from '@kibalabs/web3-react';
// import { useMutation, useQuery, useQueryClient, UseQueryResult } from '@tanstack/react-query';

// import { useAuth } from '../AuthContext';
// import { AgentAction, AgentWalletSnapshot, LeaderboardEntry, Wallet, WalletHistoricPosition, YieldOption } from '../client/resources';
// import { useGlobals } from '../GlobalsContext';

// const SECONDS_IN_MILLIS = 1000;
// const MINUTES_IN_SECONDS = 60;

// export const useYieldOptionsQuery = (staleSeconds: number = 60 * MINUTES_IN_SECONDS): UseQueryResult<YieldOption[], Error> => {
//   const { yieldSeekerClient } = useGlobals();
//   const chainId = useWeb3ChainId();
//   const actualChainId: number = chainId || 8453;
//   const assetAddress = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913';
//   return useQuery({
//     queryKey: ['yieldOptions', chainId, assetAddress],
//     queryFn: async (): Promise<YieldOption[]> => {
//       return yieldSeekerClient.listYieldOptions(actualChainId, assetAddress);
//     },
//     staleTime: staleSeconds * SECONDS_IN_MILLIS,
//     refetchOnWindowFocus: false,
//   });
// };

// export const useUserWalletQuery = (staleSeconds: number = 10 * MINUTES_IN_SECONDS): UseQueryResult<Wallet, Error> => {
//   const { authToken } = useAuth();
//   const { yieldSeekerClient } = useGlobals();
//   const account = useWeb3Account();
//   const chainId = useWeb3ChainId();
//   const actualChainId: number = chainId || 8453;
//   return useQuery({
//     queryKey: ['userWallet', account?.address, actualChainId],
//     queryFn: async (): Promise<Wallet> => {
//       if (!account?.address || !authToken) {
//         throw new Error('No wallet address or auth token available');
//       }
//       return yieldSeekerClient.getWallet(actualChainId, account.address, authToken);
//     },
//     enabled: !!(account?.address && authToken),
//     staleTime: staleSeconds * SECONDS_IN_MILLIS,
//   });
// };

// export const useAgentWalletQuery = (staleSeconds: number = 10 * MINUTES_IN_SECONDS): UseQueryResult<Wallet, Error> => {
//   const { user, currentAgentId, authToken } = useAuth();
//   const { yieldSeekerClient } = useGlobals();
//   return useQuery({
//     queryKey: ['agentWallet', user?.userId, currentAgentId],
//     queryFn: async (): Promise<Wallet> => {
//       if (!user?.userId || !currentAgentId || !authToken) {
//         throw new Error('Missing required authentication data');
//       }
//       return yieldSeekerClient.getAgentWallet(user.userId, currentAgentId, authToken);
//     },
//     enabled: !!(user?.userId && currentAgentId && authToken),
//     staleTime: staleSeconds * SECONDS_IN_MILLIS,
//   });
// };

// export const useAgentWalletOnChainQuery = (chainId: number, staleSeconds: number = 10 * MINUTES_IN_SECONDS): UseQueryResult<Wallet | null, Error> => {
//   const { user, currentAgentId, authToken } = useAuth();
//   const { yieldSeekerClient } = useGlobals();
//   const { data: agentWallet } = useAgentWalletQuery();

//   return useQuery({
//     queryKey: ['agentWalletOnChain', chainId, agentWallet?.walletAddress],
//     queryFn: async (): Promise<Wallet | null> => {
//       if (!user?.userId || !currentAgentId || !authToken || !agentWallet?.walletAddress) {
//         return null;
//       }
//       try {
//         return await yieldSeekerClient.getWallet(chainId, agentWallet.walletAddress, authToken);
//       } catch (error) {
//         console.error(`Failed to fetch agent wallet on chain ${chainId}:`, error);
//         return null;
//       }
//     },
//     enabled: !!(user?.userId && currentAgentId && authToken && agentWallet?.walletAddress),
//     staleTime: staleSeconds * SECONDS_IN_MILLIS,
//   });
// };

// type UseAgentSnapshotQueryResult = Omit<UseQueryResult<AgentWalletSnapshot, Error>, 'isLoading' | 'isFetching'> & {
//   isLoading: boolean;
//   isFetching: boolean;
//   refresh: (forceRefresh?: boolean) => Promise<AgentWalletSnapshot>;
// };

// export const useAgentSnapshotQuery = (staleSeconds: number = 10 * MINUTES_IN_SECONDS): UseAgentSnapshotQueryResult => {
//   const { user, currentAgentId, authToken } = useAuth();
//   const { yieldSeekerClient } = useGlobals();
//   const queryClient = useQueryClient();

//   const query = useQuery({
//     queryKey: ['agentSnapshot', user?.userId, currentAgentId],
//     queryFn: async (): Promise<AgentWalletSnapshot> => {
//       if (!user?.userId || !currentAgentId || !authToken) {
//         throw new Error('Missing required authentication data');
//       }
//       return yieldSeekerClient.getAgentSnapshot(user.userId, currentAgentId, authToken, false, true);
//     },
//     enabled: !!(user?.userId && currentAgentId && authToken),
//     staleTime: staleSeconds * SECONDS_IN_MILLIS,
//   });

//   const refreshMutation = useMutation({
//     mutationFn: async (forceRefresh?: boolean): Promise<AgentWalletSnapshot> => {
//       if (!user?.userId || !currentAgentId || !authToken) {
//         throw new Error('Missing required authentication data');
//       }
//       return yieldSeekerClient.getAgentSnapshot(user.userId, currentAgentId, authToken, forceRefresh ?? true, true);
//     },
//     onSuccess: (data: AgentWalletSnapshot): void => {
//       queryClient.setQueryData(['agentSnapshot', user?.userId, currentAgentId], data);
//     },
//   });

//   return {
//     ...query,
//     refresh: refreshMutation.mutateAsync,
//     isLoading: query.isLoading || refreshMutation.isPending,
//     isFetching: query.isFetching || refreshMutation.isPending,
//   };
// };

// export const useAgentWalletHistoricPositionQuery = (staleSeconds: number = 60 * MINUTES_IN_SECONDS): UseQueryResult<WalletHistoricPosition, Error> => {
//   const { user, currentAgentId, authToken } = useAuth();
//   const { yieldSeekerClient } = useGlobals();
//   return useQuery({
//     queryKey: ['agentWalletHistoricPosition', user?.userId, currentAgentId],
//     queryFn: async (): Promise<WalletHistoricPosition> => {
//       if (!user?.userId || !currentAgentId || !authToken) {
//         throw new Error('Missing required authentication data');
//       }
//       return yieldSeekerClient.getAgentWalletHistoricPosition(user.userId, currentAgentId, authToken);
//     },
//     enabled: !!(user?.userId && currentAgentId && authToken),
//     staleTime: staleSeconds * SECONDS_IN_MILLIS,
//   });
// };

// export const useAgentActionsQuery = (staleSeconds: number = 60 * MINUTES_IN_SECONDS): UseQueryResult<AgentAction[], Error> => {
//   const { user, currentAgentId, authToken } = useAuth();
//   const { yieldSeekerClient } = useGlobals();
//   return useQuery({
//     queryKey: ['agentActions', user?.userId, currentAgentId],
//     queryFn: async (): Promise<AgentAction[]> => {
//       if (!user?.userId || !currentAgentId || !authToken) {
//         throw new Error('Missing required authentication data');
//       }
//       return yieldSeekerClient.getAgentActions(user.userId, currentAgentId, authToken);
//     },
//     enabled: !!(user?.userId && currentAgentId && authToken),
//     staleTime: staleSeconds * SECONDS_IN_MILLIS,
//   });
// };

// export const useLeaderboardEntriesQuery = (limit: number, offset: number, staleSeconds: number = 10 * MINUTES_IN_SECONDS): UseQueryResult<LeaderboardEntry[], Error> => {
//   const { yieldSeekerClient } = useGlobals();
//   return useQuery({
//     queryKey: ['leaderboardEntries', limit, offset],
//     queryFn: async (): Promise<LeaderboardEntry[]> => {
//       return yieldSeekerClient.listLeaderboardEntries(limit, offset);
//     },
//     staleTime: staleSeconds * SECONDS_IN_MILLIS,
//     refetchOnReconnect: true,
//   });
// };

// export const useUserLeaderboardEntryQuery = (staleSeconds: number = 10 * MINUTES_IN_SECONDS): UseQueryResult<LeaderboardEntry, Error> => {
//   const { user, authToken } = useAuth();
//   const { yieldSeekerClient } = useGlobals();
//   return useQuery({
//     queryKey: ['userLeaderboardEntry', user?.userId],
//     queryFn: async (): Promise<LeaderboardEntry> => {
//       if (!user?.userId || !authToken) {
//         throw new Error('Missing required authentication data');
//       }
//       return yieldSeekerClient.getUserLeaderboardEntry(user.userId, authToken);
//     },
//     enabled: !!(user?.userId && authToken),
//     staleTime: staleSeconds * SECONDS_IN_MILLIS,
//     refetchOnReconnect: true,
//   });
// };

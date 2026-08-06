import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import * as A from "@/lib/api";

export const useItems = () => useQuery({ queryKey: ["items"], queryFn: A.getItems });
export const useListings = () => useQuery({ queryKey: ["listings"], queryFn: A.getListings });
export const useEvents = () => useQuery({ queryKey: ["events"], queryFn: A.getEvents });
export const usePerformance = () => useQuery({ queryKey: ["performance"], queryFn: A.getPerformance });
export const useSuggestions = (status) => useQuery({ queryKey: ["suggestions", status || "all"], queryFn: () => A.getSuggestions(status) });
export const useBriefLatest = () => useQuery({ queryKey: ["brief"], queryFn: A.getBriefLatest });
export const useFinancials = () => useQuery({ queryKey: ["financials"], queryFn: A.getFinancials });
export const useNotifications = (unread) => useQuery({ queryKey: ["notifications", unread ? "unread" : "all"], queryFn: () => A.getNotifications(unread) });
export const useAnalytics = () => useQuery({ queryKey: ["analytics"], queryFn: A.getAnalytics });
export const usePerformanceIntel = () => useQuery({ queryKey: ["perf-intel"], queryFn: A.getPerformanceIntelligence });

function invalidateAll(qc) {
  ["items", "listings", "events", "performance", "suggestions", "brief", "perf-intel", "notifications", "inbox", "financials"].forEach((k) =>
    qc.invalidateQueries({ queryKey: [k] }));
}

export function useCreateItem() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: A.createItem, onSuccess: () => invalidateAll(qc) });
}
export function useMarkItemSold() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ id, d }) => A.markItemSold(id, d), onSuccess: () => invalidateAll(qc) });
}
export function useMarkItemUnsold() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (id) => A.markItemUnsold(id), onSuccess: () => invalidateAll(qc) });
}
export function useGenerateListing() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: A.generateListing, onSuccess: () => invalidateAll(qc) });
}
export function useAnalyzeAll() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: A.runAnalysisJob, onSuccess: () => invalidateAll(qc) });
}
export function useSetItemStage() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ id, stage }) => A.setItemStage(id, stage), onSuccess: () => invalidateAll(qc) });
}
export function useUploadItemImage() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ id, data }) => A.uploadItemImage(id, data), onSuccess: () => invalidateAll(qc) });
}
export function useMarkAllNotificationsRead() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: A.markAllNotificationsRead, onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }) });
}
export function useDraftReply() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ id, text }) => A.draftReply(id, text), onSuccess: () => invalidateAll(qc) });
}
export function useMarkInboxRead() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: A.markInboxRead, onSuccess: () => invalidateAll(qc) });
}
export function useImportCsv() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: A.importCsv, onSuccess: () => invalidateAll(qc) });
}
export function useInviteMember() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ wid, d }) => A.inviteMember(wid, d), onSuccess: () => qc.invalidateQueries({ queryKey: ["members"] }) });
}
export function useRemoveMember() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ wid, memberId }) => A.removeMember(wid, memberId), onSuccess: () => qc.invalidateQueries({ queryKey: ["members"] }) });
}
export function useAnalyzeItem() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: A.analyzeItem, onSuccess: () => invalidateAll(qc) });
}
export function useApplySuggestion() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: A.applySuggestion, onSuccess: () => invalidateAll(qc) });
}
export function useDismissSuggestion() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: A.dismissSuggestion, onSuccess: () => invalidateAll(qc) });
}
export function useGenerateBrief() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: A.generateBrief, onSuccess: () => invalidateAll(qc) });
}

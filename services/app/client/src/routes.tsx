export const APP_ROUTES = {
  browse: "/browse",
  timeline: "/timeline",
} as const;

export const APP_ROUTE_CONFIG = [
  { path: APP_ROUTES.browse, mode: "browse" as const },
  { path: APP_ROUTES.timeline, mode: "timeline" as const },
] as const;

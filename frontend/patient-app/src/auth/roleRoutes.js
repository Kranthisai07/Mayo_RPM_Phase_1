export const getHomeRouteForRole = (role) => {
  switch (role) {
    case "nurse":
      return "/(nurse)/patients";
    case "admin":
      return "/(admin)/dashboard";
    case "patient":
    default:
      return "/(patient)/vitals";
  }
};

import { Outlet } from "react-router";

function MainLayout() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <Outlet />
    </div>
  );
}

export default MainLayout;
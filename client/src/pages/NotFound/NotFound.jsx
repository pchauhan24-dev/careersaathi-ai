import { Link } from "react-router";

function NotFound() {
  return (
    <main className="flex min-h-screen items-center justify-center px-6">
      <section className="text-center">
        <p className="text-sm font-semibold text-blue-300">Error 404</p>

        <h1 className="mt-4 text-4xl font-bold">Page not found</h1>

        <p className="mt-4 text-slate-400">
          The page you requested does not exist or may have been moved.
        </p>

        <Link
          className="mt-8 inline-flex rounded-xl bg-blue-500 px-5 py-3 font-semibold text-white transition hover:bg-blue-400"
          to="/"
        >
          Return to home
        </Link>
      </section>
    </main>
  );
}

export default NotFound;
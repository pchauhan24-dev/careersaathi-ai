import { FileSearch, MessageSquareText, Mic2, Sparkles } from "lucide-react";

const features = [
  {
    title: "Résumé Intelligence",
    description:
      "Analyse your résumé, identify important skills, and receive useful improvement suggestions.",
    icon: FileSearch,
  },
  {
    title: "Job Matching",
    description:
      "Compare your résumé with a target job description and discover missing skills.",
    icon: Sparkles,
  },
  {
    title: "AI Mock Interviews",
    description:
      "Practise personalized technical, HR, and behavioural interview questions.",
    icon: MessageSquareText,
  },
  {
    title: "Voice Interviews",
    description:
      "Answer questions using your voice and receive structured performance feedback.",
    icon: Mic2,
  },
];

function Home() {
  return (
    <main className="min-h-screen px-6 py-16">
      <section className="mx-auto max-w-6xl">
        <div className="mx-auto max-w-3xl text-center">
          <span className="inline-flex rounded-full border border-blue-400/30 bg-blue-400/10 px-4 py-2 text-sm font-semibold text-blue-300">
            CareerSaathi AI
          </span>

          <h1 className="mt-6 text-4xl font-bold tracking-tight sm:text-6xl">
            Your AI partner from résumé to interview
          </h1>

          <p className="mt-6 text-base leading-7 text-slate-400 sm:text-lg">
            Improve your résumé, understand job requirements, practise
            personalized interviews, and receive clear performance feedback.
          </p>
        </div>

        <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {features.map((feature) => {
            const Icon = feature.icon;

            return (
              <article
                key={feature.title}
                className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6"
              >
                <div className="inline-flex rounded-xl bg-blue-500/10 p-3 text-blue-300">
                  <Icon aria-hidden="true" size={22} />
                </div>

                <h2 className="mt-5 text-lg font-semibold">{feature.title}</h2>

                <p className="mt-3 text-sm leading-6 text-slate-400">
                  {feature.description}
                </p>
              </article>
            );
          })}
        </div>
      </section>
    </main>
  );
}

export default Home;
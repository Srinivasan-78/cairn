import { Head } from '@inertiajs/react'
import SettingsLayout from '~/layouts/SettingsLayout'

export default function SupportPage() {
  return (
    <SettingsLayout>
      <Head title="Support the Project | Cairn" />
      <div className="xl:pl-72 w-full">
        <main className="px-12 py-6 max-w-4xl">
          <h1 className="text-4xl font-semibold mb-4">Support the Project</h1>
          <p className="text-text-muted mb-10 text-lg">
            Cairn is 100% free and open source — no subscriptions, no paywalls, no catch.
            If you'd like to help keep the project going, here are a few ways to show your support.
          </p>

          {/* Other Ways to Help */}
          <section className="mb-10">
            <h2 className="text-2xl font-semibold mb-3">Ways to Help</h2>
            <ul className="space-y-2 text-text-muted">
              <li>
                <a
                  href="https://github.com/Srinivasan-78/cairn"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  Star the project on GitHub
                </a>
                {' '}— it helps more people discover Cairn
              </li>
              <li>
                <a
                  href="https://github.com/Srinivasan-78/cairn/issues"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  Report bugs and suggest features
                </a>
                {' '}— every report makes Cairn better
              </li>
              <li>Share Cairn with someone who'd use it — word of mouth is the best marketing</li>
              <li>
                <a
                  href="https://github.com/Srinivasan-78/cairn/discussions"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  Join GitHub Discussions
                </a>
                {' '}— hang out, share your build, help other users
              </li>
            </ul>
          </section>

        </main>
      </div>
    </SettingsLayout>
  )
}

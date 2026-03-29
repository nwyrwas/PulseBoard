// PulseBoard Dashboard — main page layout

// Here we are importing each component that we created to display on the main page.
// Pulling code from other files so we can use it here.

// We like to have separate files for each component
  // Primarily so each component has its own logic, data fetching, loading states, and error handling
  // If one breaks it does not break/affect the other components.
import Navbar from "./components/Navbar";
import TrendingTopics from "./components/TrendingTopics";
import PostFeed from "./components/PostFeed";
import NewsFeed from "./components/NewsFeed";


// Export default means that this is the main thing the file exports
  // In next.js the app router looks for a default export and renders it as a page
export default function Home() {
  return (

    // Layout 
    // className utilizing Tailwind CSS utility classes.
      // min-h-screen - minimum height is the full screen height
      // bg-gray-950 - background color
      // max-w-7x1 - maximum width of 80 rem (Prevents contents from stretching too wide on large screens)
      // mx-auto - center horizontally with auto margins
      // p-6 - padding on all sides
      // space-y-6 - vertical spacing between child elements
      // grid grid-cols1 md:grid-cols2 gap-6 - is our responsive grid
        // grid-cols-1 - one column on mobile
        // md:grid-cols-2 - two columns on medium screens and above. 
        // md: - tailwinds breakpoint prefix
          // apply this at medium screen width and above
          // so that postfeed and newsfeed stack vertically on mobile and sit side by side on desktop
    <div className="min-h-screen bg-gray-950">
      <Navbar />
      <main className="max-w-7xl mx-auto p-6 space-y-6">
        <TrendingTopics />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <PostFeed />
          <NewsFeed />
        </div>
      </main>
    </div>
  );
}

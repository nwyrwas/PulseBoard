// "use client" - tells next.js that this component runs in the browser
// Primarily because we are using useState and useEffect which are hooks that only work in the browser.

"use client";
import { useState, useEffect } from "react";

export default function Navbar() {

  //useState - creates a piece of state, which is a value that react tracks and re-renders when component changes.
    // useState(null) - starts with a value of null

    // set to null first due to hydration safety reason
    // which means that next.js renders components on the server side then react takes over.
        // for example if you called newDate().toLocaleTimeString() on the server and again on the client. you would get two different strings.
          // Which would cause a mismatch that cause a React hydration error.

      // Starting with null is safe for both the server and client side.

  const [lastUpdated, setLastUpdated] = useState(null);

  // useEffect only runs in the browser after hydration and sets the real time. 

  // Only runs after the component renders in the browser.
  // Takes 2 arguements. The function to run and a dependency array
  useEffect(() => {

    // sets the time when the component first loads replacing the null value
    setLastUpdated(new Date().toLocaleTimeString());

    // setInterval - is a built-in browser function that runs a callback on a repeating schedule
      // 60000 - 60000 miliseconds  = 60 seconds
      // so every 60 seconds it updates
      // lastUpdated timestamp in the navbar ticks forward every minute automatically
    const interval = setInterval(() => {
      setLastUpdated(new Date().toLocaleTimeString());
    }, 60000);

    // cleanup function
      // When a component is removed from the page clearInterval stops the repeating timer.
      // Examples are navigating away, closing the tab, etc.
      // You want to cleanup, because if not done it can cause memory leaks due to setLastUpdated can still run on a component that no longer exists.
    return () => clearInterval(interval);

    // The empty [], runs this exactly once when the component first mounts.
    // If we put something like [count] in the array it would re-run every time count changes.
  }, []);

  // flex justify-between items-center - tailwind classes working together
    // flex - turns the nav into a flexbox container
    // justify-between - pushes the two children h1 and the span to the opposit ends of the navbar.
    // items-center - vertically centers them.

  // lastUpdated || "loading..." - JSXs way of evaluating a JavaScript expression inside HTML utilizing the OR operator
    // so if lastUpdated is null or any flasy value, we want to show "Loading..." instead.
    // once useEffect runs and sets the real time, lastUpdated becomes a string.
  return (
    <nav className="bg-gray-900 border-b border-gray-700 px-6 py-4 flex justify-between items-center">
      <h1 className="text-2xl font-bold text-white">PulseBoard</h1>
      <span className="text-sm text-gray-400">
        Last updated: {lastUpdated || "Loading..."}
      </span>
    </nav>
  );
}

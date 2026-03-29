

"use client";
import useSWR from "swr";

// SWR needs a "fetcher" function — this just wraps fetch() and returns JSON
// Arrow function => - shorter way to write a function in Javascript
  // where it takes a url, then calls the browser's builtin- fetch() to make a HTTP GET Request
  // Waits for the request, then calls .json and parses into a Javascript object.

  // .then is a promise chain.
  // fetch() returns a promise - meaning it doesnt have data yet but it will in the future
  // .then - states that once the fetch() is finished to run the function with the result.
const fetcher = (url) => fetch(url).then((res) => res.json());


// SWR over useEffect
  // if we used useEffect we would have to write useState for the data, loading, and error
  // useEffect with fetch inside it and a setInterval for auto-refresh

  // we use SWR Because it replaces all of that in one hook.
export default function TrendingTopics() {

  // SWR - Stale While Revalidate
    // show cached data immediately while fetching fresh data in the background.
    // so the user always see somethign on the screen without seeing a blank screen on loads.


    // data - fetched data, undefined when first loading from the API while loading
    // error - any error that occured, if undefined it means it was successful
    // isLoading - true only during the first fetch, false after
  const { data, error, isLoading } = useSWR(

    // url - cache key and endpoint to fetch from
    // fetcher function - getting the data
    // refresh every 60 seconds
    "http://localhost:8000/trending",
    fetcher,
    { refreshInterval: 60000 } // re-fetch every 60 seconds
  );

  // Utilizing these because it provides simple feedback UI
    // guard clause pattern.

    // if the Trending Topics API is down, PostFeed and NewsFeed are unaffected.
  if (isLoading) return <div className="text-gray-400 p-4">Loading trends...</div>;
  if (error) return <div className="text-red-400 p-4">Failed to load trends</div>;

  // Find the max mention count for scaling the bars

  // data?.length - if data exists access .length. If data is null or undefined, return undefined instead of crashing.
    // Guarding against the moment between SWR finishing on loading and when the data is available.

  // Ternary ? ... 1 - means that if data has items, calculate the max if not default to 1
    // Preventing a division by 0 when dividng by maxCount

  // Math.max(...data.map((t) => t.mention_count)) - data.map((t) => t.mention_count)
    // loops through every topic and pulls out just the mention count in an array
    // then finds the highest number
    // the ... spread operator unpacts the arry into individual arguments because Math.max expects separate nubmers and not an array.
  const maxCount = data?.length ? Math.max(...data.map((t) => t.mention_count)) : 1;



  // data?.map() - if data exists, loop through it.
  // key={topic.topic} - React requires a unique key prop on every item in a list
    // React uses this to track which items were changed,added or removed when the data updates. 
        // Without this react can update the DOM efficiently and will warn you

  // capitalize - capitalizes the first letter of the topic name.

  // style={{ width: `${(topic.mention_count / maxCount) * 100}%` }}
    // inline style in react
      // {} - this is a javaScript expression
      // width is the template literal calculating the percentage
        // dividing the max count by mention count by 100 giving a string like "65%"

  // rounded-full h-2 on the progress bar container
  // bg-blue-500 h-2 rounded-full on the fill.
    // creates the pill-shaped progress bar.
    // gray container is always full width, blue fill shrins based on the calculated percentage
  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h2 className="text-xl font-bold text-white mb-4">Trending Topics</h2>
      <div className="space-y-3">
        {data?.map((topic) => (
          <div key={topic.topic} className="flex items-center gap-4">
            <span className="text-gray-400 font-mono w-6">#{topic.topic_rank}</span>
            <div className="flex-1">
              <div className="flex justify-between mb-1">
                <span className="text-white font-medium capitalize">{topic.topic}</span>
                <span className="text-gray-400 text-sm">{topic.mention_count} mentions</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full"
                  style={{ width: `${(topic.mention_count / maxCount) * 100}%` }}
                ></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

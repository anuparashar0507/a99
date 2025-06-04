import React from "react";

type Props = {
  jsonString: string;
};

const JsonDisplay: React.FC<Props> = ({ jsonString }) => {
  let parsedData: Record<string, any> = {};
  if (
    typeof jsonString === "string" &&
    jsonString.trim().startsWith("```json")
  ) {
    const jsonMatch = jsonString.trim().match(/```json\s*([\s\S]*?)```/i);
    if (jsonMatch && jsonMatch[1]) {
      try {
        parsedData = JSON.parse(jsonMatch[1]);
      } catch (error) {
        return (
          <div className="bg-red-100 text-red-700 p-4 rounded-md">
            Invalid JSON:{" "}
            {error instanceof Error ? error.message : "Unknown error"}
          </div>
        );
      }
    }
  } else if (typeof value === "string" && !value.trim().startsWith("```json")) {
    try {
      parsedData = JSON.parse(jsonString);
    } catch (error) {
      return (
        <div className="bg-red-100 text-red-700 p-4 rounded-md">
          Invalid JSON:{" "}
          {error instanceof Error ? error.message : "Unknown error"}
        </div>
      );
    }
  }

  console.log(parsedData);

  return (
    <div className="bg-white shadow-md rounded-xl p-6 space-y-6 text-gray-800">
      {Object.entries(parsedData).map(([key, value]) => (
        <div key={key}>
          <h2 className="text-xl font-semibold capitalize mb-2 text-indigo-600">
            {key.replace(/_/g, " ")}
          </h2>

          {Array.isArray(value) ? (
            <ul className="list-disc list-inside space-y-1 pl-4">
              {value.map((item, idx) => (
                <li key={idx} className="text-gray-700">
                  {item}
                </li>
              ))}
            </ul>
          ) : typeof value === "string" && value.includes("1.") ? (
            <ul className="list-inside space-y-2 pl-4">
              {value
                .split(/(?=\d+\.\s)/)
                .filter(Boolean)
                .map((item, idx) => (
                  <li key={idx} className="text-gray-700">
                    {item.trim()}
                  </li>
                ))}
            </ul>
          ) : (
            <p className="text-gray-700 whitespace-pre-line">{value}</p>
          )}
        </div>
      ))}
    </div>
  );
};

export default JsonDisplay;

import React, {useEffect, useState} from "react";
import { useOutletContext } from "react-router-dom";

const SettingsPage: React.FC = () => {
   return (
     <div className="h-full bg-gray-100 p-6 flex items-center justify-center">
        <div className="bg-white shadow-xl rounded-2xl p-8 max-w-md w-full">
           <h1 className="text-2xl font-bold mb-4 text-gray-800">Settings</h1>
           <p className="text-gray-600">
              Welcome to your Settings.
           </p>
        </div>
     </div>
   )
};
export default SettingsPage;
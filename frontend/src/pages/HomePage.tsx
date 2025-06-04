import React from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { PlusIcon } from "lucide-react";

const HomePage: React.FC = () => {
   return (
     <div className="h-full flex flex-col">
        <header className="border-b p-6 flex justify-between items-center">
           <div>
              <h1 className="text-2xl font-semibold">Welcome to Marketing Agent</h1>
              <p className="text-muted-foreground text-sm mt-2">
                 Get started by selecting a topic from the Topic menu
              </p>
           </div>
           <Link to="/topic">
              <Button className="bg-purple-600 hover:bg-purple-700">
                 <PlusIcon className="h-4 w-4 mr-2"/>
                 Go to Topics
              </Button>
           </Link>
        </header>
        <div className="flex-1 flex items-center justify-center p-6">
           <div className="text-center space-y-4 max-w-2xl">
              <h2 className="text-3xl font-bold text-gray-900">Your AI-Powered Marketing Assistant</h2>
              <p className="text-lg text-gray-600">
                 Create compelling blogs, generate engaging content, and elevate your brand voice with our
                 intelligent content creation platform.
              </p>
           </div>
        </div>
     </div>
   );
};

export default HomePage;
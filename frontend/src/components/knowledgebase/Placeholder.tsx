import React from 'react';

interface PlaceholderProps {
   title: string;
   subtitle: string;
}

const Placeholder: React.FC<PlaceholderProps> = ({ title, subtitle }) => {
   return (
     <div className="flex flex-col items-center justify-center h-96 text-center">
        <img
          src="/knowledgebase.svg"
          alt="Empty"
          className="w-50 h-50"
        />
        <h2 className="text-2xl pb-1.5 font-semibold">{title}</h2>
        <p className="text-gray-500 text-sm">{subtitle}</p>
     </div>
   );
};

export default Placeholder;
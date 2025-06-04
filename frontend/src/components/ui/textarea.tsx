import * as React from "react"

import { cn } from "@/lib/utils"
import {useRef, useState} from "react";
import {
   DropdownMenu,
   DropdownMenuContent,
   DropdownMenuItem,
   DropdownMenuTrigger
} from "@radix-ui/react-dropdown-menu";
import { Braces } from "lucide-react";

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
   variables?: string[];
   textValue?: string | number;
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, onChange, variables, textValue, ...props }) => {

     const [text, setText] = useState<string | number>(textValue)
     const [showDropdown, setShowDropdown] = useState<boolean>(false);
     const [dropdownPosition, setDropdownPosition] = useState<{
        x: number;
        y: number;
     }>({ x: 0, y: 0 });
     const [cursorIndex, setCursorIndex] = useState<number>(0);
     const textareaRef = useRef<HTMLTextAreaElement | null>(null);

     const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setText(e.target.value);
        const cursorPos = e.target.selectionStart;
        setCursorIndex(cursorPos);

        // Check for "{" to show dropdown
        if (e.target.value[cursorPos - 1] === "{") {
           const textarea = textareaRef.current;
           if (textarea) {
              const { x, y } = getCaretCoordinates(textarea, cursorPos);
              setDropdownPosition({ x, y });
              setShowDropdown(true);
           }
        } else {
           setShowDropdown(false);
        }

        if (onChange) {
           onChange(e);
        }
     }

     const insertVariable = (variable: string) => {
        if (typeof text !== "number") {
           const beforeCursor = text.slice(0, cursorIndex);
           const afterCursor = text.slice(cursorIndex);
           const newText = `${beforeCursor}${variable}}${afterCursor}`;
           setText(newText);
           setShowDropdown(false);
        }
     };

     const getCaretCoordinates = (
       textarea: HTMLTextAreaElement,
       cursorPos: number
     ) => {
        const div = document.createElement("div");
        const style = window.getComputedStyle(textarea);

        // Copy textarea styles to the div
        Array.from(style).forEach((key) => {
           div.style.setProperty(key, style.getPropertyValue(key));
        });

        div.style.position = "absolute";
        div.style.visibility = "hidden";
        div.style.whiteSpace = "pre-wrap";
        div.style.wordWrap = "break-word";

        div.textContent = textarea.value.slice(0, cursorPos);
        if (textarea.value[cursorPos - 1] === "\n") {
           div.textContent += "\u200b";
        }

        document.body.appendChild(div);
        const { offsetWidth, offsetHeight } = div;
        const { offsetLeft, offsetTop } = textarea;
        const x = offsetLeft + offsetWidth;
        const y = offsetTop + offsetHeight;
        document.body.removeChild(div);

        return { x, y };
     };

     return (
       <div>
         <textarea
           className={cn(
             "flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
             className
           )}
           ref={textareaRef}
           value={text}
           onChange={handleTextChange}
           {...props}
         />
          {variables?.length ? (
            <DropdownMenu open={showDropdown} onOpenChange={setShowDropdown}>
               <DropdownMenuTrigger></DropdownMenuTrigger>
               <DropdownMenuContent
                 side="left"
                 className={cn(
                   "relative bg-white min-w-[180px] rounded-lg shadow-lg border border-gray-100 py-1 overflow-hidden",
                   `top-[${dropdownPosition.y}]`,
                   `left-[${dropdownPosition.x}]`
                 )}
                 sideOffset={5}
               >
                  {variables?.map((variable) => (
                    <DropdownMenuItem
                      className={cn("flex items-center px-3 py-1.5 text-sm hover:bg-gray-50 cursor-pointer transition-colors focus:bg-gray-50 focus:outline-none")}
                      onClick={() => insertVariable(variable)}>
                      <span className="mr-2 text-blue-500">
                       <Braces className="h-4 w-4"/>
                     </span>
                       <span className="text-gray-700">{variable}</span>
                    </DropdownMenuItem>
                  ))}
               </DropdownMenuContent>
            </DropdownMenu>
          ) : null}
       </div>
     )
  }
)
Textarea.displayName = "Textarea"

export { Textarea }
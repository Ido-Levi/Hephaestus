import * as React from "react"
import { cn } from "@/lib/utils"

const ScrollArea = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, children, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("relative overflow-auto", className)}
    {...props}
  >
    {children}
  </div>
))
ScrollArea.displayName = "ScrollArea"

const ScrollBar = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { orientation?: "horizontal" | "vertical" }
>(({ className, orientation = "vertical", ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "absolute",
      orientation === "horizontal" ? "bottom-0 left-0 right-0 h-2" : "right-0 top-0 bottom-0 w-2",
      className
    )}
    {...props}
  />
))
ScrollBar.displayName = "ScrollBar"

export { ScrollArea, ScrollBar }
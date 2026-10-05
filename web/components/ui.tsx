import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";
// Small shadcn/ui-style primitive: Radix Slot + CVA, kept local and accessible.
const variants = cva("button", {
  variants: {
    variant: { default: "primary", outline: "outline", ghost: "ghost" },
  },
  defaultVariants: { variant: "default" },
});
export function Button({
  className,
  variant,
  asChild = false,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof variants> & { asChild?: boolean }) {
  const Comp = asChild ? Slot : "button";
  return (
    <Comp
      className={twMerge(clsx(variants({ variant }), className))}
      {...props}
    />
  );
}
export function Empty({
  title = "Ainda não há dados",
  text = "A fonte selecionada não contém informações para esta visão.",
}: {
  title?: string;
  text?: string;
}) {
  return (
    <div className="empty">
      <span>◌</span>
      <h3>{title}</h3>
      <p>{text}</p>
    </div>
  );
}

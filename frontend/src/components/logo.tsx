import Image from "next/image"
import Link from "next/link"

interface LogoProps {
  size?: number
  showText?: boolean
  className?: string
  href?: string
}

export function Logo({
  size = 32,
  showText = true,
  className = "",
  href
}: LogoProps) {
  const logoElement = (
    <div className={`flex items-center space-x-3 ${className}`}>
      <Image
        src="/logo.jpg"
        alt="JobFlow Pro Logo"
        width={size}
        height={size}
        className="rounded-lg"
      />
      {showText && (
        <span className="text-xl font-bold text-foreground">JobFlow Pro</span>
      )}
    </div>
  )

  if (href) {
    return (
      <Link href={href}>
        {logoElement}
      </Link>
    )
  }

  return logoElement
} 
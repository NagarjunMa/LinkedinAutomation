export interface SkillCategory {
  name: string
  skills: string[]
}

export interface SkillDatabase {
  programming_languages: string[]
  frameworks_libraries: string[]
  tools_platforms: string[]
}

export const PROGRAMMING_LANGUAGES = [
  // Popular languages first
  "JavaScript",
  "TypeScript",
  "Python",
  "Java",
  "C#",
  "C++",
  "Go",
  "Rust",
  "Swift",
  "Kotlin",
  "PHP",
  "Ruby",
  "SQL",
  "HTML",
  "CSS",

  // Less common but important
  "C",
  "R",
  "Scala",
  "Clojure",
  "Haskell",
  "Erlang",
  "Elixir",
  "F#",
  "Dart",
  "Lua",
  "Perl",
  "Shell/Bash",
  "PowerShell",
  "Assembly",
  "MATLAB",
  "Objective-C",
  "Visual Basic",
  "COBOL",
  "Fortran",
  "Julia",
  "Zig"
]

export const FRAMEWORKS_LIBRARIES = [
  // Frontend Frameworks
  "React",
  "Vue.js",
  "Angular",
  "Svelte",
  "Next.js",
  "Nuxt.js",
  "Gatsby",
  "Remix",

  // Backend Frameworks
  "Express.js",
  "Nest.js",
  "FastAPI",
  "Django",
  "Flask",
  "Spring Boot",
  "ASP.NET Core",
  "Ruby on Rails",
  "Laravel",
  "Symfony",
  "Phoenix",
  "Gin",
  "Echo",
  "Fiber",

  // Mobile Frameworks
  "React Native",
  "Flutter",
  "Ionic",
  "Xamarin",
  "Cordova",

  // Data Science/ML
  "TensorFlow",
  "PyTorch",
  "scikit-learn",
  "Pandas",
  "NumPy",
  "Matplotlib",
  "Seaborn",
  "Plotly",
  "Keras",
  "OpenCV",
  "spaCy",
  "NLTK",

  // JavaScript Libraries
  "jQuery",
  "D3.js",
  "Three.js",
  "Chart.js",
  "Lodash",
  "Moment.js",
  "Socket.io",
  "Axios",

  // CSS Frameworks
  "Tailwind CSS",
  "Bootstrap",
  "Material-UI",
  "Chakra UI",
  "Ant Design",
  "Bulma",

  // Testing
  "Jest",
  "Cypress",
  "Playwright",
  "Selenium",
  "Pytest",
  "JUnit",
  "Mocha",
  "Chai",

  // Others
  "jQuery",
  "Electron",
  "GraphQL",
  "Apollo",
  "Prisma",
  "TypeORM",
  "Sequelize",
  "Mongoose"
]

export const TOOLS_PLATFORMS = [
  // Cloud Platforms
  "AWS",
  "Google Cloud Platform",
  "Microsoft Azure",
  "DigitalOcean",
  "Heroku",
  "Vercel",
  "Netlify",
  "Railway",
  "Render",

  // DevOps & CI/CD
  "Docker",
  "Kubernetes",
  "Jenkins",
  "GitHub Actions",
  "GitLab CI/CD",
  "CircleCI",
  "Travis CI",
  "Terraform",
  "Ansible",
  "Vagrant",

  // Databases
  "PostgreSQL",
  "MySQL",
  "MongoDB",
  "Redis",
  "SQLite",
  "Oracle",
  "SQL Server",
  "DynamoDB",
  "Cassandra",
  "Elasticsearch",
  "Firebase",
  "Supabase",

  // Version Control
  "Git",
  "GitHub",
  "GitLab",
  "Bitbucket",
  "Mercurial",

  // IDEs & Editors
  "Visual Studio Code",
  "IntelliJ IDEA",
  "Eclipse",
  "Sublime Text",
  "Atom",
  "Vim",
  "Emacs",
  "WebStorm",
  "PyCharm",
  "Android Studio",
  "Xcode",

  // Project Management
  "Jira",
  "Confluence",
  "Trello",
  "Asana",
  "Monday.com",
  "Notion",
  "Linear",

  // Design Tools
  "Figma",
  "Sketch",
  "Adobe XD",
  "Photoshop",
  "Illustrator",
  "Canva",

  // API Tools
  "Postman",
  "Insomnia",
  "Thunder Client",

  // Monitoring & Analytics
  "Google Analytics",
  "Mixpanel",
  "Amplitude",
  "Sentry",
  "DataDog",
  "New Relic",
  "LogRocket",

  // Communication
  "Slack",
  "Discord",
  "Teams",
  "Zoom",

  // Operating Systems
  "Linux",
  "Ubuntu",
  "CentOS",
  "macOS",
  "Windows",

  // Web Servers
  "Nginx",
  "Apache",
  "IIS",

  // Message Queues
  "RabbitMQ",
  "Apache Kafka",
  "Amazon SQS",
  "Redis Pub/Sub",

  // Containers & Orchestration
  "Docker Compose",
  "Docker Swarm",
  "Helm",
  "OpenShift",

  // Serverless
  "AWS Lambda",
  "Vercel Functions",
  "Netlify Functions",
  "Cloudflare Workers"
]

export const skillsDatabase: SkillDatabase = {
  programming_languages: PROGRAMMING_LANGUAGES,
  frameworks_libraries: FRAMEWORKS_LIBRARIES,
  tools_platforms: TOOLS_PLATFORMS
}

export function searchSkills(query: string, category: keyof SkillDatabase, limit = 10): string[] {
  if (!query.trim()) return []

  const skills = skillsDatabase[category]
  const lowercaseQuery = query.toLowerCase()

  // Exact matches first
  const exactMatches = skills.filter(skill =>
    skill.toLowerCase() === lowercaseQuery
  )

  // Starts with matches
  const startsWithMatches = skills.filter(skill =>
    skill.toLowerCase().startsWith(lowercaseQuery) &&
    !exactMatches.includes(skill)
  )

  // Contains matches
  const containsMatches = skills.filter(skill =>
    skill.toLowerCase().includes(lowercaseQuery) &&
    !exactMatches.includes(skill) &&
    !startsWithMatches.includes(skill)
  )

  return [...exactMatches, ...startsWithMatches, ...containsMatches].slice(0, limit)
}

export function getAllSkillsForCategory(category: keyof SkillDatabase): string[] {
  return skillsDatabase[category]
}

export function isValidSkill(skill: string, category: keyof SkillDatabase): boolean {
  return skillsDatabase[category].includes(skill)
}

export function getPopularSkills(category: keyof SkillDatabase, limit = 10): string[] {
  // Return the first N skills (which are ordered by popularity)
  return skillsDatabase[category].slice(0, limit)
}
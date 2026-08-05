/**
 * Готовые наборы слов для фильтра профиля: стеки, грейды и смежные роли.
 * Подставляются в поля «есть» и «исключить», на классификатор чатов не влияют.
 */

export type ProfilePreset = {
  label: string
  include: string
  exclude?: string
}

export type ProfileGroup = {
  id: string
  label: string
  presets: ProfilePreset[]
}

export const PROFILE_GROUPS: ProfileGroup[] = [
  {
    id: 'frontend',
    label: 'Frontend',
    presets: [
      { label: 'Junior Frontend', include: 'junior, frontend' },
      { label: 'Middle Frontend', include: 'middle, frontend' },
      { label: 'Senior Frontend', include: 'senior, frontend' },
      { label: 'Lead Frontend', include: 'lead, frontend' },
      { label: 'Frontend Vue', include: 'frontend, vue' },
      { label: 'Frontend React', include: 'frontend, react' },
      { label: 'Frontend Angular', include: 'frontend, angular' },
      { label: 'Frontend TypeScript', include: 'frontend, typescript' },
      { label: 'Frontend Next.js', include: 'frontend, next' },
      { label: 'Frontend Nuxt', include: 'frontend, nuxt' },
      { label: 'Верстальщик', include: 'верстальщик, html, css' },
      { label: 'Frontend без Битрикс', include: 'frontend', exclude: 'битрикс, bitrix, 1с' },
    ],
  },
  {
    id: 'backend',
    label: 'Backend',
    presets: [
      { label: 'Junior Backend', include: 'junior, backend' },
      { label: 'Middle Backend', include: 'middle, backend' },
      { label: 'Senior Backend', include: 'senior, backend' },
      { label: 'Lead Backend', include: 'lead, backend' },
      { label: 'Backend Python', include: 'backend, python' },
      { label: 'Backend Django', include: 'python, django' },
      { label: 'Backend FastAPI', include: 'python, fastapi' },
      { label: 'Backend Node', include: 'backend, node' },
      { label: 'Backend Java', include: 'backend, java' },
      { label: 'Backend Go', include: 'backend, golang' },
      { label: 'Backend C#/.NET', include: 'backend, c#, .net' },
      { label: 'Backend PHP', include: 'backend, php' },
      { label: 'Backend без 1С', include: 'backend', exclude: '1с, 1c, битрикс' },
    ],
  },
  {
    id: 'fullstack',
    label: 'Fullstack',
    presets: [
      { label: 'Junior Fullstack', include: 'junior, fullstack' },
      { label: 'Middle Fullstack', include: 'middle, fullstack' },
      { label: 'Senior Fullstack', include: 'senior, fullstack' },
      { label: 'Fullstack JS', include: 'fullstack, javascript' },
      { label: 'Fullstack Node + React', include: 'fullstack, node, react' },
      { label: 'Fullstack Python', include: 'fullstack, python' },
      { label: 'Fullstack без Битрикс', include: 'fullstack', exclude: 'битрикс, bitrix, 1с' },
    ],
  },
  {
    id: 'mobile',
    label: 'Mobile',
    presets: [
      { label: 'Junior Mobile', include: 'junior, mobile' },
      { label: 'Middle Mobile', include: 'middle, mobile' },
      { label: 'Senior Mobile', include: 'senior, mobile' },
      { label: 'iOS Swift', include: 'ios, swift' },
      { label: 'Android Kotlin', include: 'android, kotlin' },
      { label: 'Flutter', include: 'flutter' },
      { label: 'React Native', include: 'react native' },
    ],
  },
  {
    id: 'devops',
    label: 'DevOps',
    presets: [
      { label: 'Junior DevOps', include: 'junior, devops' },
      { label: 'Middle DevOps', include: 'middle, devops' },
      { label: 'Senior DevOps', include: 'senior, devops' },
      { label: 'SRE', include: 'sre' },
      { label: 'Kubernetes', include: 'kubernetes, k8s' },
      { label: 'AWS', include: 'aws, devops' },
      { label: 'Terraform', include: 'terraform' },
      { label: 'CI/CD', include: 'ci/cd, devops' },
    ],
  },
  {
    id: 'data',
    label: 'Data / ML',
    presets: [
      { label: 'Junior Data Analyst', include: 'junior, аналитик данных' },
      { label: 'Data Analyst', include: 'data analyst, аналитик' },
      { label: 'Data Engineer', include: 'data engineer' },
      { label: 'Middle Data Scientist', include: 'middle, data scientist' },
      { label: 'Senior Data Scientist', include: 'senior, data scientist' },
      { label: 'ML Engineer', include: 'ml engineer, machine learning' },
      { label: 'ETL / SQL', include: 'sql, etl' },
      { label: 'BI / Power BI', include: 'power bi, bi' },
    ],
  },
  {
    id: 'qa',
    label: 'QA',
    presets: [
      { label: 'Junior QA', include: 'junior, qa' },
      { label: 'Middle QA', include: 'middle, qa' },
      { label: 'Senior QA', include: 'senior, qa' },
      { label: 'Manual QA', include: 'qa, ручное' },
      { label: 'AQA / Auto', include: 'автотестиров, aqa' },
      { label: 'QA Python', include: 'qa, python' },
      { label: 'QA Java', include: 'qa, java' },
    ],
  },
  {
    id: 'design',
    label: 'Design',
    presets: [
      { label: 'Junior Designer', include: 'junior, дизайн' },
      { label: 'Middle Designer', include: 'middle, дизайн' },
      { label: 'Senior Designer', include: 'senior, дизайн' },
      { label: 'UI/UX', include: 'ui, ux' },
      { label: 'Product Designer', include: 'product designer' },
      { label: 'Figma', include: 'figma, дизайн' },
      { label: 'Graphic Design', include: 'графический дизайн' },
      { label: 'Motion', include: 'motion, анимац' },
    ],
  },
  {
    id: 'product',
    label: 'Product / Project',
    presets: [
      { label: 'Junior Product', include: 'junior, product manager' },
      { label: 'Product Manager', include: 'product manager' },
      { label: 'Senior Product', include: 'senior, product' },
      { label: 'Project Manager', include: 'project manager, менеджер проектов' },
      { label: 'Scrum Master', include: 'scrum' },
      { label: 'Business Analyst', include: 'business analyst, бизнес-аналитик' },
      { label: 'System Analyst', include: 'системный аналитик' },
    ],
  },
  {
    id: 'marketing',
    label: 'Marketing',
    presets: [
      { label: 'Junior Marketing', include: 'junior, маркетинг' },
      { label: 'Digital Marketing', include: 'digital, маркетинг' },
      { label: 'SMM', include: 'smm' },
      { label: 'Performance / PPC', include: 'ppc, performance' },
      { label: 'SEO', include: 'seo' },
      { label: 'Content', include: 'контент, копирайт' },
      { label: 'Email / CRM marketing', include: 'email, crm маркетинг' },
      { label: 'Brand Manager', include: 'brand manager, бренд' },
    ],
  },
  {
    id: 'sales',
    label: 'Sales / HR',
    presets: [
      { label: 'Sales Manager', include: 'менеджер по продажам' },
      { label: 'Account Manager', include: 'account manager' },
      { label: 'B2B Sales', include: 'b2b, продаж' },
      { label: 'Recruiter', include: 'рекрутер, recruiter' },
      { label: 'HR Manager', include: 'hr, менеджер по персоналу' },
      { label: 'Talent Acquisition', include: 'talent acquisition' },
    ],
  },
  {
    id: 'onec',
    label: '1С / ERP',
    presets: [
      { label: '1С Junior', include: 'junior, 1с' },
      { label: '1С Middle', include: 'middle, 1с' },
      { label: '1С Senior', include: 'senior, 1с' },
      { label: '1С Разработчик', include: '1с, разработчик' },
      { label: '1С Аналитик', include: '1с, аналитик' },
      { label: 'Битрикс', include: 'битрикс' },
      { label: 'SAP', include: 'sap' },
    ],
  },
  {
    id: 'security',
    label: 'Security / Support',
    presets: [
      { label: 'InfoSec', include: 'информационной безопасности, infosec' },
      { label: 'AppSec', include: 'appsec, application security' },
      { label: 'SOC / Analyst', include: 'soc, security' },
      { label: 'Support L1', include: 'поддержк, l1' },
      { label: 'Support L2', include: 'поддержк, l2' },
      { label: 'Sysadmin', include: 'системный администратор' },
    ],
  },
  {
    id: 'grades',
    label: 'Грейды',
    presets: [
      { label: 'Стажёр / Intern', include: 'стажёр, intern' },
      { label: 'Junior', include: 'junior' },
      { label: 'Middle', include: 'middle' },
      { label: 'Senior', include: 'senior' },
      { label: 'Lead', include: 'lead' },
      { label: 'Head / Director', include: 'head, director, руководитель' },
      { label: 'Principal / Staff', include: 'principal, staff' },
    ],
  },
]

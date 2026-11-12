import {
  Activity as ActivitySvg,
  AlertCircle as AlertCircleSvg,
  AlertTriangle as AlertTriangleSvg,
  ArrowLeft as ArrowLeftSvg,
  ArrowRight as ArrowRightSvg,
  Award as AwardSvg,
  BarChart3 as BarChart3Svg,
  BookOpen as BookOpenSvg,
  Car as CarSvg,
  Check as CheckSvg,
  CheckCircle2 as CheckCircle2Svg,
  ChevronDown as ChevronDownSvg,
  ChevronRight as ChevronRightSvg,
  ChevronUp as ChevronUpSvg,
  Clock as ClockSvg,
  Cloud as CloudSvg,
  Coffee as CoffeeSvg,
  Compass as CompassSvg,
  Cpu as CpuSvg,
  Database as DatabaseSvg,
  DollarSign as DollarSignSvg,
  Download as DownloadSvg,
  ExternalLink as ExternalLinkSvg,
  Eye as EyeSvg,
  FileJson as FileJsonSvg,
  FileSpreadsheet as FileSpreadsheetSvg,
  FileText as FileTextSvg,
  Globe as GlobeSvg,
  Home as HomeSvg,
  Info as InfoSvg,
  Laptop as LaptopSvg,
  Layers as LayersSvg,
  LineChart as LineChartSvg,
  Loader2 as Loader2Svg,
  Megaphone as MegaphoneSvg,
  Menu as MenuSvg,
  Package as PackageSvg,
  PlusCircle as PlusCircleSvg,
  Printer as PrinterSvg,
  Search as SearchSvg,
  ShieldAlert as ShieldAlertSvg,
  ShieldCheck as ShieldCheckSvg,
  Shirt as ShirtSvg,
  Sliders as SlidersSvg,
  Smartphone as SmartphoneSvg,
  Star as StarSvg,
  Sun as SunSvg,
  Moon as MoonSvg,
  Volume2 as Volume2Svg,
  VolumeX as VolumeXSvg,
  RefreshCw as RefreshCwSvg,
  MessageSquare as MessageSquareSvg,
  Send as SendSvg,
  Table as TableSvg,
  Tag as TagSvg,
  Target as TargetSvg,
  TrendingDown as TrendingDownSvg,
  TrendingUp as TrendingUpSvg,
  Upload as UploadSvg,
  UserCheck as UserCheckSvg,
  X as XSvg,
  XCircle as XCircleSvg,
  Zap as ZapSvg,
  type LucideProps
} from 'lucide-react';

const registry = {
  Activity: ActivitySvg,
  AlertCircle: AlertCircleSvg,
  AlertTriangle: AlertTriangleSvg,
  ArrowLeft: ArrowLeftSvg,
  ArrowRight: ArrowRightSvg,
  Award: AwardSvg,
  BarChart3: BarChart3Svg,
  BookOpen: BookOpenSvg,
  Brain: BarChart3Svg,
  Car: CarSvg,
  Check: CheckSvg,
  CheckCircle2: CheckCircle2Svg,
  ChevronDown: ChevronDownSvg,
  ChevronRight: ChevronRightSvg,
  ChevronUp: ChevronUpSvg,
  Clock: ClockSvg,
  Cloud: CloudSvg,
  Coffee: CoffeeSvg,
  Compass: CompassSvg,
  Cpu: CpuSvg,
  Database: DatabaseSvg,
  DollarSign: DollarSignSvg,
  Download: DownloadSvg,
  ExternalLink: ExternalLinkSvg,
  Eye: EyeSvg,
  FileJson: FileJsonSvg,
  FileSpreadsheet: FileSpreadsheetSvg,
  FileText: FileTextSvg,
  Globe: GlobeSvg,
  Home: HomeSvg,
  Info: InfoSvg,
  Laptop: LaptopSvg,
  Layers: LayersSvg,
  LineChart: LineChartSvg,
  Loader2: Loader2Svg,
  Megaphone: MegaphoneSvg,
  Menu: MenuSvg,
  Package: PackageSvg,
  PlusCircle: PlusCircleSvg,
  Printer: PrinterSvg,
  Search: SearchSvg,
  ShieldAlert: ShieldAlertSvg,
  ShieldCheck: ShieldCheckSvg,
  Shirt: ShirtSvg,
  Sliders: SlidersSvg,
  Smartphone: SmartphoneSvg,
  Sparkles: CompassSvg,
  Star: StarSvg,
  Sun: SunSvg,
  Moon: MoonSvg,
  Volume2: Volume2Svg,
  VolumeX: VolumeXSvg,
  RefreshCw: RefreshCwSvg,
  MessageSquare: MessageSquareSvg,
  Send: SendSvg,
  Table: TableSvg,
  Tag: TagSvg,
  Target: TargetSvg,
  TrendingDown: TrendingDownSvg,
  TrendingUp: TrendingUpSvg,
  Upload: UploadSvg,
  UserCheck: UserCheckSvg,
  X: XSvg,
  XCircle: XCircleSvg,
  Zap: ZapSvg,
  analytics: BarChart3Svg,
  upload: UploadSvg,
  trend: TrendingUpSvg,
  risk: ShieldAlertSvg,
  revenue: DollarSignSvg
} as const;

export type IconName = keyof typeof registry;
export type AppIconProps = LucideProps & { name: IconName };

/** Outline SVGs share stroke/currentColor and hide decorative graphics from AT. */
export function AppIcon({ name, size = 24, ...props }: AppIconProps) {
  const Icon = registry[name];
  const labelled = Boolean(props['aria-label'] || props['aria-labelledby']);
  return (
    <Icon
      size={size}
      strokeWidth={1.75}
      focusable="false"
      role={labelled ? 'img' : undefined}
      aria-hidden={labelled ? undefined : true}
      {...props}
    />
  );
}

export const Activity = (props: LucideProps) => <AppIcon {...props} name="Activity" />;
export const AlertCircle = (props: LucideProps) => <AppIcon {...props} name="AlertCircle" />;
export const AlertTriangle = (props: LucideProps) => <AppIcon {...props} name="AlertTriangle" />;
export const ArrowLeft = (props: LucideProps) => <AppIcon {...props} name="ArrowLeft" />;
export const ArrowRight = (props: LucideProps) => <AppIcon {...props} name="ArrowRight" />;
export const Award = (props: LucideProps) => <AppIcon {...props} name="Award" />;
export const BarChart3 = (props: LucideProps) => <AppIcon {...props} name="BarChart3" />;
export const BookOpen = (props: LucideProps) => <AppIcon {...props} name="BookOpen" />;
export const Brain = (props: LucideProps) => <AppIcon {...props} name="Brain" />;
export const Car = (props: LucideProps) => <AppIcon {...props} name="Car" />;
export const Check = (props: LucideProps) => <AppIcon {...props} name="Check" />;
export const CheckCircle2 = (props: LucideProps) => <AppIcon {...props} name="CheckCircle2" />;
export const ChevronDown = (props: LucideProps) => <AppIcon {...props} name="ChevronDown" />;
export const ChevronRight = (props: LucideProps) => <AppIcon {...props} name="ChevronRight" />;
export const ChevronUp = (props: LucideProps) => <AppIcon {...props} name="ChevronUp" />;
export const Clock = (props: LucideProps) => <AppIcon {...props} name="Clock" />;
export const Cloud = (props: LucideProps) => <AppIcon {...props} name="Cloud" />;
export const Coffee = (props: LucideProps) => <AppIcon {...props} name="Coffee" />;
export const Compass = (props: LucideProps) => <AppIcon {...props} name="Compass" />;
export const Cpu = (props: LucideProps) => <AppIcon {...props} name="Cpu" />;
export const Database = (props: LucideProps) => <AppIcon {...props} name="Database" />;
export const DollarSign = (props: LucideProps) => <AppIcon {...props} name="DollarSign" />;
export const Download = (props: LucideProps) => <AppIcon {...props} name="Download" />;
export const ExternalLink = (props: LucideProps) => <AppIcon {...props} name="ExternalLink" />;
export const Eye = (props: LucideProps) => <AppIcon {...props} name="Eye" />;
export const FileJson = (props: LucideProps) => <AppIcon {...props} name="FileJson" />;
export const FileSpreadsheet = (props: LucideProps) => <AppIcon {...props} name="FileSpreadsheet" />;
export const FileText = (props: LucideProps) => <AppIcon {...props} name="FileText" />;
export const Globe = (props: LucideProps) => <AppIcon {...props} name="Globe" />;
export const Home = (props: LucideProps) => <AppIcon {...props} name="Home" />;
export const Info = (props: LucideProps) => <AppIcon {...props} name="Info" />;
export const Laptop = (props: LucideProps) => <AppIcon {...props} name="Laptop" />;
export const Layers = (props: LucideProps) => <AppIcon {...props} name="Layers" />;
export const LineChart = (props: LucideProps) => <AppIcon {...props} name="LineChart" />;
export const Loader2 = (props: LucideProps) => <AppIcon {...props} name="Loader2" />;
export const Megaphone = (props: LucideProps) => <AppIcon {...props} name="Megaphone" />;
export const Menu = (props: LucideProps) => <AppIcon {...props} name="Menu" />;
export const Package = (props: LucideProps) => <AppIcon {...props} name="Package" />;
export const PlusCircle = (props: LucideProps) => <AppIcon {...props} name="PlusCircle" />;
export const Printer = (props: LucideProps) => <AppIcon {...props} name="Printer" />;
export const Search = (props: LucideProps) => <AppIcon {...props} name="Search" />;
export const ShieldAlert = (props: LucideProps) => <AppIcon {...props} name="ShieldAlert" />;
export const ShieldCheck = (props: LucideProps) => <AppIcon {...props} name="ShieldCheck" />;
export const Shirt = (props: LucideProps) => <AppIcon {...props} name="Shirt" />;
export const Sliders = (props: LucideProps) => <AppIcon {...props} name="Sliders" />;
export const Smartphone = (props: LucideProps) => <AppIcon {...props} name="Smartphone" />;
export const Sparkles = (props: LucideProps) => <AppIcon {...props} name="Sparkles" />;
export const Star = (props: LucideProps) => <AppIcon {...props} name="Star" />;
export const Sun = (props: LucideProps) => <AppIcon {...props} name="Sun" />;
export const Moon = (props: LucideProps) => <AppIcon {...props} name="Moon" />;
export const Volume2 = (props: LucideProps) => <AppIcon {...props} name="Volume2" />;
export const VolumeX = (props: LucideProps) => <AppIcon {...props} name="VolumeX" />;
export const RefreshCw = (props: LucideProps) => <AppIcon {...props} name="RefreshCw" />;
export const MessageSquare = (props: LucideProps) => <AppIcon {...props} name="MessageSquare" />;
export const Send = (props: LucideProps) => <AppIcon {...props} name="Send" />;
export const Table = (props: LucideProps) => <AppIcon {...props} name="Table" />;
export const Tag = (props: LucideProps) => <AppIcon {...props} name="Tag" />;
export const Target = (props: LucideProps) => <AppIcon {...props} name="Target" />;
export const TrendingDown = (props: LucideProps) => <AppIcon {...props} name="TrendingDown" />;
export const TrendingUp = (props: LucideProps) => <AppIcon {...props} name="TrendingUp" />;
export const Upload = (props: LucideProps) => <AppIcon {...props} name="Upload" />;
export const UserCheck = (props: LucideProps) => <AppIcon {...props} name="UserCheck" />;
export const X = (props: LucideProps) => <AppIcon {...props} name="X" />;
export const XCircle = (props: LucideProps) => <AppIcon {...props} name="XCircle" />;
export const Zap = (props: LucideProps) => <AppIcon {...props} name="Zap" />;

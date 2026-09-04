package
{
   import flash.display.Bitmap;
   import flash.display.BitmapData;
   import flash.display.DisplayObject;
   import flash.display.DisplayObjectContainer;
   import flash.display.Shape;
   import flash.display.Sprite;
   import flash.display.Stage;
   import flash.events.Event;
   import flash.events.KeyboardEvent;
   import flash.events.MouseEvent;
   import flash.filesystem.File;
   import flash.filesystem.FileMode;
   import flash.filesystem.FileStream;
   import flash.filters.BlurFilter;
   import flash.geom.ColorTransform;
   import flash.geom.Matrix;
   import flash.geom.Point;
   import flash.geom.Rectangle;
   import flash.text.TextField;
   import flash.text.TextFieldAutoSize;
   import flash.ui.Keyboard;
   import flash.utils.Dictionary;
   import flash.utils.getTimer;
   import flash.utils.getQualifiedClassName;

   import fe.World;
   import fe.Obj;
   import fe.Pt;
   import fe.loc.Location;
   import fe.loc.Tile;
   import fe.unit.Pers;
   import fe.unit.Unit;
   import fe.unit.UnitPlayer;
   import fe.weapon.Weapon;

   /**
    * RealisticVision v0.3 —— 视野系统模组。
    *
    * v0.3：
    * - 软雾：4×4 子格低分辨率雾图 + 高斯模糊（去锯齿），脏标记门控。
    * - 性能：FOV 仅在玩家移动/墙体变化/周期兜底时重算；雾图仅在淡入淡出
    *   变化时重绘；掩膜按 FOV 版本 + 包围盒签名门控；显示树扫描提前退出。
    * - 看门狗：onFrame 全程 try/catch，连续错误自动禁用模组（防错误风暴卡死）。
    *
    * 文档类。由补丁后 MainFE 加载并调用静态 RealisticVisionMod.init(main)。
    */
   public class RealisticVisionMod extends Sprite
   {
      // ---- 默认配置（可被 config.txt 覆盖）----
      private var cfgEnabled:Boolean = true;
      private var cfgMode:String = "current";   // vanilla=原版 / classic=v0.7.2 / current=当前
      private var cfgDim:Number = 0.35;
      private var cfgDoorDim:Number = 0.5;      // 透光门/水后视野的亮度（比记忆暗色亮）
      private var cfgLitMin:Number = 0.6;
      private var cfgFadeStep:Number = 0.1;
      private var cfgMaskBlurClassic:Number = 6.0; // 敌人掩膜模糊（classic，子格 px=5px；0=硬边）
      private var cfgMaskBlurCurrent:Number = 4.0; // 敌人掩膜模糊（current，与雾层 curBlur 对齐）
      private var cfgTeleGrace:Number = 3;
      private var cfgBaseRooms:Object = {};
      private var cfgDebug:Boolean = false;

      // 发布门禁第 2 项：启动日志版本标记（fileLog init 行携带，防"线上跑旧构建"）
      private static const VERSION:String = "v0.25.5";

      private static const FOV_VISIBLE:int = 2;
      private static const FOV_DIM:int = 1;
      private static const FOV_NONE:int = 0;

      private static const WALL_NEIGHBORS:Array = [[-1,-1],[0,-1],[1,-1],[-1,0],[1,0],[-1,1],[0,1],[1,1]];

      private static const ARM_SCAN_R:Number = 64;

      // 瓦片 4 角采样的子格中心偏移（current 模式分类用，避免每瓦片分配数组）
      private static const CORNER_OFFS_X:Array = [0.5,FOG_SUB - 0.5];
      private static const CORNER_OFFS_Y:Array = [0.5,FOG_SUB - 0.5];

      // 雾图参数：current（线状）模式用 8×8 子格（5px）+ 每子格独立 castRay——
      // 阴影边界由光线几何产生连续线状（无阶梯）；classic（仿原版）用模糊+
      // 钳制（共用位图，块粒度变细但视觉不变）。
      private static const FOG_SUB:int = 8;
      private static const FOG_PAD:int = 4;

      // 敌人 FOV 掩膜参数：每瓦片 8px 子格（5px，与雾层一致）。掩膜 = 矢量
      // Shape + 模糊位图填充 + cacheAsBitmap（v0.24.4：alpha 掩膜须双方
      // cacheAsBitmap=true，否则掩膜忽略 alpha/位图填充 → 二分；模糊按模式
      // 对齐雾层边界宽度，敌人明暗交界渐变淡出）；区域外扩覆盖血条（头顶）
      // 与动画超出手臂/翅膀等超出逻辑包围盒的视觉部分
      private static const MASK_SUB:int = 8;
      // current 掩膜采样 fogCache 的亮度阈值（v0.24.5）：门景(≤128)/亮部
      // (<140) 可见；记忆区(166)/未探索(255)/暗部(≥140) 不可见
      private static const MASK_LIT_A:int = 140;
      private static const MASK_PAD_X:int = 2;
      private static const MASK_PAD_TOP:int = 3;
      private static const MASK_PAD_BOTTOM:int = 1;

      private static var inst:RealisticVisionMod;

      /** 游戏调用入口（静态）。 */
      public static function init(main:*):void
      {
         inst = new RealisticVisionMod();
         inst.startup(main);
      }

      private var stageRef:Stage;

      // 房间状态
      private var curLoc:Location = null;
      private var spaceX:int = 0;
      private var spaceY:int = 0;
      private var fov:Array;
      private var explored:Array;
      private var visCur:Array;
      private var br:Array;   // 连续亮度（原版渐变）：LOS 亮度 × 距离衰减
      private var litArr:Array; // 瓦片 LOS 亮度（1-累计遮光，0..1；墙=1）
      // 子格级"曾见过"历史（0/1）：记忆区↔未探索边界按 5px 子格粒度，而非 40px 瓦片
      private var seenSub:Array;
      private var subW:int = 0;

      // FOV 门控
      private var fovVersion:int = 0;
      private var lastGX:Number = -99999;
      private var lastGY:Number = -99999;
      private var lastStructHash:int = 0;
      private var lastFovFrame:int = -100;   // v0.24.7：fov 重算节流（moved 触发的最小间隔帧）
      private var fogBlurPending:Boolean = false; // v0.24.7：模糊+钳制拆帧（fov 帧峰值减半）
      private var eyeX:Number = 0;
      private var eyeY:Number = 0;
      private var locDist1:Number = 300;
      private var locDist2:Number = 1000;

      // 自建雾层：原版式瓦片掩膜（无空间模糊，边界为干脆瓦片线）
      private var fogVis:Sprite = null;
      private var fogRaw:BitmapData = null;   // classic 覆盖层/current 工作位图
      private var fogCache:BitmapData = null; // current：最终 alpha 场缓存（仅 FOV 重算时更新）
      private var fogBmp:BitmapData = null;
      private var fogBitmap:Bitmap = null;
      // classic（仿原版）v7：1px/瓦片雾层——复刻原版 lightBmp 结构
      // （smoothing 双线性 + 半格错位 + 游戏 visi 渐进节奏 → 原版雾状感）
      private var classicRaw:BitmapData = null;
      private var classicBmp:Bitmap = null;
      // 墙专用层（v0.25.4）：2px/瓦片、整层位移 (-tileX/2,-tileY/2)——每墙
      // 只写 (2x+1,2y+1) 一格自身公式值，该格在位移下恰好精确覆盖整瓦片、
      // 零溢出。v0.25.2/3 的 4 格写法有 W/N 溢出格（墙值画进邻地板 20px =
      // 边缘亮带/脏迹）；v0.25.1 的四分格象限采样发脏。雾层墙像素=协调值
      // 只服务地板侧平滑，墙的屏上显示完全由本层承担
      private var wallRaw:BitmapData = null;
      private var wallBmp:Bitmap = null;
      private var lastA:Array = null;   // 每瓦片上次写入 classicRaw 的 alpha（变化才写像素）
      private var aArr:Array = null;    // 每瓦片本帧公式值（墙层单值采样源）
      private var wallKey:Array = null; // 墙层每瓦片 key（变化才写像素）
      private var memCur:Array = null;  // classic：每瓦片记忆化进度（0=游戏值，1=记忆区 dimA，0.1/帧渐变）
      // 跨房间记忆（v0.22）：loc.id → explored 数组（原版靠 tile.visi 缓存
      // 保留已探索常亮；模组自己的 explored[] 需随房间切换保存/恢复，否则
      // 回到房间时全部按未探索处理）
      private var roomMem:Object = {};
      private var fogDirty:Boolean = false;
      private var fogRect:Rectangle = null;
      private var fogCellRect:Rectangle = new Rectangle(0,0,FOG_SUB,FOG_SUB);
      private var fogPoint:Point = new Point(0,0);
      private var fogCellPoint:Point = new Point(0,0);
      private var fogBlur:BlurFilter = new BlurFilter(2.0,2.0,2);   // classic（仿原版）半影
      private var curBlur:BlurFilter = new BlurFilter(4.0,4.0,3);   // current：阴影渐变过渡（≈32px 世界）
      // 敌人掩膜模糊（v0.24.3）：按模式对齐各自雾层边界的模糊策略——
      // BlurFilter(bx,q) ≈ 盒模糊 bx px 应用 q 次，σ = bx·√(q/12) 子格：
      // classic 目标 40px（1px/瓦片双线性渐变）→ 6.0/q2（σ≈12px）；current
      // 目标 32px（雾层 curBlur）→ 4.0/q3（σ≈10px，与雾层同参）。0=硬边
      private var maskBlurClassic:BlurFilter = new BlurFilter(6.0,6.0,2);
      private var maskBlurCurrent:BlurFilter = new BlurFilter(4.0,4.0,3);

      private var defCT:ColorTransform = new ColorTransform();
      private var infraCT:ColorTransform = new ColorTransform(1,1,1,1,100);

      // 敌人显示状态：unit -> {state:int, m2:Shape, m3:Shape, m2d:BitmapData,
      // m2e:BitmapData, lastFov:int, lastBb:String}（m2d/m2e=掩膜二值场/模糊场）
      private var unitVis:Dictionary = new Dictionary(true);
      // 被我们强制隐藏血条的单位
      private var hpHidden:Dictionary = new Dictionary(true);
      // 显示树扫描：被我们隐藏的非单位子对象（狮鹫手臂等）
      private var managedHidden:Dictionary = new Dictionary(true);
      private var managedCount:int = 0;

      // 念力宽限倒计时
      private var teleGraceFrames:int = 0;
      private var teleLast:Object = null;

      // 看门狗
      private var errCount:int = 0;

      // 调试
      private var dbgTxt:TextField = null;
      private var dbgOn:Boolean = false;
      private var frameCount:int = 0;
      private var lastFrameMs:int = 0;
      private var normalApplied:Boolean = false;
      private var toastTxt:TextField = null;
      private var toastFrames:int = 0;

      // 自动化验证埋点（config autotest=1 启用；默认关，不影响正常游玩）。
      // 每 300 帧输出一行窗口统计 autoStats()，事件（进房/念力抓放/F 键/
      // 看门狗）即时输出——验证 v0.24.7 五处优化与 v0.24.6 修复的运行时证据
      private var cfgAutoTest:Boolean = false;
      private var atLastEmit:int = 0; // 上次统计输出的 frameCount（窗口差值触发）
      private var atFovM:int = 0;    // fov 重算：moved 触发（过 3 帧节流）
      private var atFovH:int = 0;    // fov 重算：结构哈希变化（墙破坏/门）
      private var atFovF:int = 0;    // fov 重算：30 帧兜底
      private var atMvThr:int = 0;   // moved 但被 3 帧节流跳过
      private var atBlurD:int = 0;   // current：模糊+钳制拆帧（延迟到次帧）
      private var atClsF:int = 0;    // classic：全图循环执行帧
      private var atClsS:int = 0;    // classic：30Hz 门控跳过帧
      private var atWsEx:int = 0;    // 武器扫描执行帧
      private var atWsSk:int = 0;    // 武器扫描门控跳过帧
      private var atMaskRaw:int = 0; // 掩膜 classicRaw 采样分支（零 raycast）
      private var atMaskRay:int = 0; // 掩膜 raycast 兜底分支
      private var atMsSum:int = 0;   // 窗口内模组帧耗时累计（ms）
      private var atMsMax:int = 0;   // 窗口内模组帧耗时峰值（ms）
      private var atE0:int = 0;      // 敌人三态计数（最近一帧快照：全隐）
      private var atE1:int = 0;      // 全显
      private var atE2:int = 0;      // 部分可见（挂掩膜）

      // 哔哔小马选项页的开关面板
      private var optPanel:Sprite = null;
      private var optTxt:TextField = null;
      // v0.25.0：注入选项页原生列表的模式行（克隆 visPipOptItem 实例，点击循环模式）
      private var optRow:Object = null;      // 注入的行实例
      private var optRowAnchor:Object = null; // 锚点行（id=="fullscreen"）——子选项卡检测用

      public function RealisticVisionMod()
      {
         super();
      }

      private function startup(main:*):void
      {
         // 文件日志（trace 在 release 构建被剥离，写 applicationStorageDirectory
         // 诊断启动卡点——RConnect 同款做法）
         var lg:String = "startup enter main=" + (main != null) + " stage=" + (main != null && main.stage != null);
         if(main == null || main.stage == null)
         {
            this.fileLog(lg + " -> NO STAGE, abort");
            trace("[RVision] init: no stage");
            return;
         }
         stageRef = main.stage;
         this.loadConfig();
         this.fileLog(lg + " -> after loadConfig enabled=" + this.cfgEnabled);
         stageRef.addEventListener(Event.ENTER_FRAME,this.onFrame);
         stageRef.addEventListener(KeyboardEvent.KEY_DOWN,this.onKeyDown);
         stageRef.addEventListener(MouseEvent.RIGHT_MOUSE_DOWN,this.onRightDown);
         trace("[RVision] init ok enabled=" + this.cfgEnabled);
         this.fileLog("init ok " + VERSION + " enabled=" + this.cfgEnabled);
      }

      /** 诊断文件日志：%APPDATA%/<appid>/Local Store/RVision.log（trace 被 release 剥离）。 */
      private function fileLog(msg:String):void
      {
         try
         {
            var f:File = File.applicationStorageDirectory.resolvePath("RVision.log");
            var fs:FileStream = new FileStream();
            fs.open(f,FileMode.APPEND);
            fs.writeUTFBytes(msg + "\n");
            fs.close();
         }
         catch(err:Error)
         {
         }
      }

      // ==================== 配置 ====================

      private function loadConfig():void
      {
         try
         {
            var f:File = File.applicationDirectory.resolvePath("mods/RealisticVision/release/config.txt");
            if(!f.exists)
            {
               return;
            }
            var fs:FileStream = new FileStream();
            fs.open(f,FileMode.READ);
            var s:String = fs.readUTFBytes(fs.bytesAvailable);
            fs.close();
            var lines:Array = s.split(/\r?\n/);
            for each(var line:String in lines)
            {
               var kv:Array = line.split("=",2);
               if(kv.length != 2)
               {
                  continue;
               }
               var key:String = kv[0];
               var val:String = kv[1];
               if(key == "enabled")
               {
                  this.cfgEnabled = val == "1";
               }
                else if(key == "dim")
                {
                   this.cfgDim = Number(val);
                }
                else if(key == "doordim")
                {
                   this.cfgDoorDim = Number(val);
                }
               else if(key == "litmin")
               {
                  this.cfgLitMin = Number(val);
               }
               else if(key == "fadestep")
               {
                  this.cfgFadeStep = Number(val);
               }
               else if(key == "maskblur_classic")
               {
                  this.cfgMaskBlurClassic = Number(val);
                  this.maskBlurClassic.blurX = this.maskBlurClassic.blurY = this.cfgMaskBlurClassic;
               }
               else if(key == "maskblur_current")
               {
                  this.cfgMaskBlurCurrent = Number(val);
                  this.maskBlurCurrent.blurX = this.maskBlurCurrent.blurY = this.cfgMaskBlurCurrent;
               }
               else if(key == "telegrace")
               {
                  this.cfgTeleGrace = Number(val);
               }
               else if(key == "base_rooms")
               {
                  var ids:Array = val.split(",");
                  for each(var id:String in ids)
                  {
                     if(id != "")
                     {
                        this.cfgBaseRooms[id] = true;
                     }
                  }
               }
               else if(key == "debug")
               {
                  this.cfgDebug = val == "1";
               }
               else if(key == "autotest")
               {
                  this.cfgAutoTest = val == "1";
               }
               else if(key == "mode")
               {
                  if(val == "vanilla" || val == "classic" || val == "current")
                  {
                     this.cfgMode = val;
                  }
               }
            }
         }
         catch(err:Error)
         {
            trace("[RVision] config read error: " + err);
         }
      }

      private function saveConfig():void
      {
         try
         {
            var f:File = File.applicationDirectory.resolvePath("mods/RealisticVision/release/config.txt");
            var fs:FileStream = new FileStream();
            fs.open(f,FileMode.WRITE);
            var ids:Array = [];
            for(var id:String in this.cfgBaseRooms)
            {
               ids.push(id);
            }
            var s:String = "enabled=" + (this.cfgEnabled ? "1" : "0") + "\n"
               + "mode=" + this.cfgMode + "\n"
               + "dim=" + this.cfgDim + "\n"
               + "doordim=" + this.cfgDoorDim + "\n"
               + "litmin=" + this.cfgLitMin + "\n"
               + "fadestep=" + this.cfgFadeStep + "\n"
               + "maskblur_classic=" + this.cfgMaskBlurClassic + "\n"
               + "maskblur_current=" + this.cfgMaskBlurCurrent + "\n"
               + "telegrace=" + this.cfgTeleGrace + "\n"
               + "base_rooms=" + ids.join(",") + "\n"
               + "debug=" + (this.cfgDebug ? "1" : "0") + "\n"
               + "autotest=" + (this.cfgAutoTest ? "1" : "0") + "\n";
            fs.writeUTFBytes(s);
            fs.close();
            if(this.cfgAutoTest)
            {
               this.fileLog("auto config saved (enabled=" + this.cfgEnabled
                  + " mode=" + this.cfgMode + ")");
            }
         }
         catch(err:Error)
         {
            trace("[RVision] config write error: " + err);
            this.fileLog("auto config write error: " + err + "\n" + err.getStackTrace());
         }
      }

      private function onKeyDown(e:KeyboardEvent):void
      {
         if(e.keyCode == Keyboard.F10)
         {
            this.dbgOn = !this.dbgOn;
            if(!this.dbgOn && this.dbgTxt)
            {
               this.dbgTxt.visible = false;
            }
         }
         else if(e.keyCode == Keyboard.F11)
         {
            this.cfgEnabled = !this.cfgEnabled;
            this.saveConfig();
            this.curLoc = null;
            this.errCount = 0;
            trace("[RVision] enabled=" + this.cfgEnabled);
            if(this.cfgAutoTest)
            {
               this.fileLog("auto key F11 enabled=" + this.cfgEnabled);
            }
         }
         else if(e.keyCode == Keyboard.F12)
         {
            // 渲染模式轮换：vanilla（原版）→ classic（v0.7.2）→ current（当前）
            if(this.cfgAutoTest)
            {
               this.fileLog("auto key F12");
            }
            this.cycleMode();
         }
         else if(e.keyCode == Keyboard.Q)
         {
            // 念力键（默认 Q）：目标为不可见敌人时拦截，游戏 Ctr 收不到
            if(this.blockInvisibleGrab())
            {
               e.stopImmediatePropagation();
            }
         }
      }

      private function onRightDown(e:MouseEvent):void
      {
         // 念力备用键（右键）：同上
         if(this.blockInvisibleGrab())
         {
            e.stopImmediatePropagation();
         }
      }

      /**
       * 复刻游戏抓取目标选择（光标 50px 内最近 levitPoss 且 massa<=maxTeleMassa 的对象）：
       * 若该对象是不可见的敌人 → 拦截输入（玩家不能隔墙选中敌人；物品不受限）。
       */
      private function blockInvisibleGrab():Boolean
      {
         var w:World = World.w;
         if(w == null || w.loc == null || w.gg == null || !this.cfgEnabled || !w.black)
         {
            return false;
         }
         var loc:Location = w.loc;
         if(loc !== this.curLoc)
         {
            return false;
         }
         var maxMassa:Number = w.pers != null ? (w.pers as Pers).maxTeleMassa : 1;
         var best:Object = null;
         var bestD:Number = 50 * 50;
         var obj:Pt = loc.firstObj;
         var guard:int = 0;
         while(obj != null && guard < 5000)
         {
            if(obj is Obj && (obj as Obj).levitPoss && (obj as Obj).massa <= maxMassa)
            {
               var dx:Number = w.celX - obj.X;
               var dy:Number = w.celY - (obj.Y - (obj as Obj).scY / 2);
               var d:Number = dx * dx + dy * dy;
               if(d < bestD)
               {
                  bestD = d;
                  best = obj;
               }
            }
            obj = obj.nobj;
            guard++;
         }
         if(best is Unit)
         {
            var bu:Unit = best as Unit;
            if(!bu.player && !bu.npc && bu.fraction != Unit.F_PLAYER)
            {
               if(this.enemyState(loc,bu) == 0)
               {
                  return true;
               }
            }
         }
         return false;
      }

      // ==================== 主循环（含看门狗） ====================

      private function onFrame(e:Event):void
      {
         var t0:int = getTimer();
         this.frameCount++;
         if(this.frameCount % 180 == 1)
         {
            // 心跳（诊断）：确认 onFrame 在跑（每 ~3 秒一行）
            this.fileLog("tick " + this.frameCount);
         }
         try
         {
            this.onFrameInner();
            this.lastFrameMs = getTimer() - t0;
            if(this.cfgAutoTest)
            {
               this.atMsSum += this.lastFrameMs;
               if(this.lastFrameMs > this.atMsMax)
               {
                  this.atMsMax = this.lastFrameMs;
               }
               // frameCount 被 debugStep 双递增（奇偶不稳），用窗口差值触发
               if(this.frameCount - this.atLastEmit >= 300)
               {
                  this.atLastEmit = this.frameCount;
                  this.autoStats();
               }
            }
            this.errCount = 0;
         }
         catch(err:Error)
         {
            this.lastFrameMs = getTimer() - t0;
            this.errCount++;
            if(this.errCount == 1)
            {
               trace("[RVision] ERROR: " + err + "\n" + err.getStackTrace());
               if(this.cfgAutoTest)
               {
                  this.fileLog("auto error #" + err + "\n" + err.getStackTrace());
                  try
                  {
                     var w:World = World.w;
                     if(w != null && w["verror"] != null)
                     {
                        this.fileLog("auto verror: " + w["verror"].txt.text);
                     }
                  }
                  catch(e2:Error)
                  {
                  }
               }
            }
            if(this.errCount > 30)
            {
               if(this.cfgEnabled)
               {
                  this.cfgEnabled = false;
                  this.saveConfig();
                  trace("[RVision] auto-disabled after repeated errors");
                  if(this.cfgAutoTest)
                  {
                     this.fileLog("auto watchdog disabled after " + this.errCount + " errors");
                  }
               }
               this.errCount = 0;
            }
         }
      }

      /** 自动化验证：每 300 帧输出一行窗口统计并复位计数器（autotest=1）。 */
      private function autoStats():void
      {
         this.fileLog("auto st f=" + this.frameCount
            + " mode=" + this.cfgMode
            + " fov=" + this.atFovM + "/" + this.atFovH + "/" + this.atFovF
            + " mvThr=" + this.atMvThr
            + " blurD=" + this.atBlurD
            + " cls=" + this.atClsF + "/" + this.atClsS
            + " ws=" + this.atWsEx + "/" + this.atWsSk
            + " mask=" + this.atMaskRaw + "/" + this.atMaskRay
            + " e=" + this.atE0 + "/" + this.atE1 + "/" + this.atE2
            + " mgr=" + this.managedCount
            + " ms=" + (this.atMsSum / 300).toFixed(2) + "/" + this.atMsMax
            + " err=" + this.errCount);
         this.atFovM = 0;
         this.atFovH = 0;
         this.atFovF = 0;
         this.atMvThr = 0;
         this.atBlurD = 0;
         this.atClsF = 0;
         this.atClsS = 0;
         this.atWsEx = 0;
         this.atWsSk = 0;
         this.atMaskRaw = 0;
         this.atMaskRay = 0;
         this.atMsSum = 0;
         this.atMsMax = 0;
      }

      private function onFrameInner():void
      {
         var w:World = World.w;
         if(w == null)
         {
            return;
         }
         if(w.allStat < 1)
         {
            if(this.curLoc != null)
            {
               this.resetOff();
            }
            return;
         }
         var loc:Location = w.loc;
         if(loc == null || !loc.active || w.gg == null)
         {
            return;
         }
         if(loc !== this.curLoc)
         {
            this.resetRoom(w,loc);
         }
         this.updateOptPanel(w);
         // 透传模式（vanilla / 总开关关 / 游戏黑暗关 / 安全基地）：游戏原生渲染，
         // 模组不碰 visi/visLight/lightBmp（原版效果原样恢复）
         if(!this.cfgEnabled || !w.black || this.cfgMode == "vanilla" || loc.base || this.cfgBaseRooms[loc.id] == true)
         {
            // v0.24.6：清除模组一切残留（掩膜/隐藏单位/隐藏武器/手臂）——
            // 否则 F12/F11 切回原版后，此前在暗处被隐藏的敌人保持隐身、
            // 过期掩膜继续裁剪单位
            this.restoreAll(w,loc);
            this.normalMode(w,loc);
            this.debugStep(w,loc,true);
            return;
         }
         // FOV 门控：玩家位移 / 阻挡结构变化（自算 opac+phis 哈希——isRelight/isRebuild
         // 在 Location.step 末尾即被游戏清零，读不到）/ 每 15 帧兜底。
         // 位移阈值 1.5px（v0.22 优化）：快速跑动时重算频率降约 3 倍（原 0.5px
         // 每帧移动都重算 → 卡顿）；边界更新滞后 ~1.5px 不可察觉
         var gg:UnitPlayer = loc.gg;
         var moved:Boolean = Math.abs(gg.X - this.lastGX) > 1.5 || Math.abs(gg.Y - this.lastGY) > 1.5;
         // v0.24.5：结构哈希每 2 帧算一次（墙破坏/开门/关门检测延迟 ≤1 帧，
         // 不可察觉；全图 1248 瓦片遍历从每帧降到半帧）
         var hash:int = (this.frameCount & 1) == 0
            ? this.structHash(loc) : this.lastStructHash;
         // v0.24.7：fov 重算节流——moved 触发的最小间隔 3 帧（快速跑动时
         // 重算频率降 ~3×；fov 帧 2-3ms 峰值是主要卡顿源，阴影边界滞后
         // ≤3 帧 ≈50ms 由雾层模糊掩盖）；墙破坏（hash 变化）与 30 帧兜底
         // 不受限（破坏墙即时更新视野）
         var needFov:Boolean = (moved && this.frameCount - this.lastFovFrame >= 3)
            || hash != this.lastStructHash || this.frameCount % 30 == 0;
         if(needFov)
         {
            if(this.cfgAutoTest)
            {
               if(hash != this.lastStructHash)
               {
                  this.atFovH++;
               }
               else if(moved)
               {
                  this.atFovM++;
               }
               else
               {
                  this.atFovF++;
               }
            }
            this.lastFovFrame = this.frameCount;
            this.lastGX = gg.X;
            this.lastGY = gg.Y;
            this.lastStructHash = hash;
            this.computeFov(loc);
            this.fovVersion++;
            this.fogDirty = true;
         }
         else if(this.cfgAutoTest && moved)
         {
            this.atMvThr++;
         }
         if(this.cfgMode == "classic")
         {
            // classic（仿原版）：雾场复刻原版亮度 + 记忆区暗化（v4 自渲染）
            this.applyVisionClassic(w,loc,needFov);
            if((this.frameCount & 1) == 0 || needFov)
            {
               this.doorBoost(w,loc);
            }
         }
         else
         {
            // current（平滑阴影）：模组自建雾层全权接管
            this.applyVision(w,loc,needFov);
         }
         this.hideEnemies(w,loc,needFov);
         if(this.frameCount % 10 == 0)
         {
            this.sweepMasks();
         }
         this.blockInvisibleHover(loc,gg);
         this.enforceTele(loc);
         this.debugStep(w,loc,false);
      }

      private function resetOff():void
      {
         this.curLoc = null;
         this.explored = [];
         this.fov = [];
         this.visCur = [];
         this.roomMem = {};   // 世界重置（读档/加载）：跨房间记忆清空
         this.unitVis = new Dictionary(true);
         this.hpHidden = new Dictionary(true);
         this.managedHidden = new Dictionary(true);
         this.managedCount = 0;
         this.lastGX = this.lastGY = -99999;
         this.lastFovFrame = -100;
         this.fogBlurPending = false;
      }

      private function resetRoom(w:World, loc:Location):void
      {
         // 跨房间记忆（v0.22）：离开前保存当前房间的 explored（最后一次
         // FOV 重算后的状态），回到同 id 房间时恢复——原版靠 tile.visi 缓存
         // 保留已探索常亮，模组需自己保存 explored[]
         if(this.curLoc != null && this.explored != null && this.explored.length > 0)
         {
            this.roomMem[this.curLoc.id] = this.explored.concat();
         }
         this.curLoc = loc;
         this.spaceX = loc.spaceX;
         this.spaceY = loc.spaceY;
         // classic v5：每瓦片 alpha 缓存随房间重置（同尺寸房间防残留）
         this.lastA = null;
         var n:int = this.spaceX * this.spaceY;
         this.fov = new Array(n);
         this.visCur = new Array(n);
         this.br = new Array(n);
         this.litArr = new Array(n);
         this.subW = this.spaceX * FOG_SUB;
         this.seenSub = new Array(this.subW * this.spaceY * FOG_SUB);
         // 恢复跨房间记忆（存在且尺寸匹配时），否则新房间全未探索
         var mem:Array = this.roomMem[loc.id] as Array;
         var hasMem:Boolean = mem != null && mem.length == n;
         this.explored = hasMem ? mem.concat() : new Array(n);
         var i:int;
         for(i = 0; i < n; i++)
         {
            this.fov[i] = FOV_NONE;
            if(!hasMem)
            {
               this.explored[i] = 0;
            }
            this.visCur[i] = 0;
            this.br[i] = 0;
            this.litArr[i] = 0;
         }
         if(hasMem)
         {
            // current 的记忆区填充按 seenSub 子格历史（fillMemoryTile）——
            // 恢复 explored 时把已探索瓦片的 seenSub 全部标记，首帧记忆区
            // 显示正确（瓦片级边界，随后 FOV 重算细化）
            var si:int;
            var sx:int;
            var sy:int;
            for(si = 0; si < n; si++)
            {
               if(this.explored[si] == 1)
               {
                  var tx0:int = si % this.spaceX;
                  var ty0:int = (si / this.spaceX) | 0;
                  var base:int = ty0 * FOG_SUB * this.subW + tx0 * FOG_SUB;
                  for(sx = 0; sx < FOG_SUB; sx++)
                  {
                     for(sy = 0; sy < FOG_SUB; sy++)
                     {
                        this.seenSub[base + sy * this.subW + sx] = 1;
                     }
                  }
               }
            }
         }
         // 透传/原版（vanilla/总开关关/黑暗关/安全基地）：visi 与掩膜完全交给游戏
         var pass:Boolean = !this.cfgEnabled || !w.black || this.cfgMode == "vanilla"
            || loc.base || this.cfgBaseRooms[loc.id] == true;
         if(!pass)
         {
            this.ensureFog(w);
            if(this.cfgMode == "classic")
            {
               // classic（v4）：雾场自渲染，隐藏游戏掩膜（模式切换时一并隐藏，
               // 避免首帧露出）
               if(w.grafon != null)
               {
                  w.grafon.visLight.visible = false;
               }
            }
            else
            {
               // current：模组接管 visi（二元：探索过=1/未探索=0，游戏逻辑语义对齐原版）
               var tx:int;
               var ty:int;
               for(tx = 0; tx < this.spaceX; tx++)
               {
                  for(ty = 0; ty < this.spaceY; ty++)
                  {
                     var t:Tile = loc.getTile(tx,ty);
                     // 只写 visi（二元），**不写 t_visi**（v0.21.1）：t_visi 是
                     // 游戏 lighting() 的目标值，保留游戏自己的值——current 退出
                     // （切 vanilla/classic/F11 关闭）后，游戏 lighting2/lighting
                     // 以 t_visi 为目标把 visi 拉回游戏语义（自愈），不会残留
                     // 模组写的 0/1 污染原版渲染
                     t.visi = 0;
                  }
               }
            }
         }
         this.fogDirty = true;
         this.fovVersion++;
         this.normalApplied = false;
         this.locDist1 = loc.lDist1 > 0 ? loc.lDist1 : 300;
         this.locDist2 = loc.lDist2 > 0 ? loc.lDist2 : 1000;
         // 置为不可能值：进房首帧强制 needFov（立即重算 fogCache，避免首帧全黑）
         this.lastGX = -99999;
         this.lastGY = -99999;
         trace("[RVision] room " + loc.id + " " + this.spaceX + "x" + this.spaceY + " lDist2=" + loc.lDist2 + " mode=" + this.cfgMode);
         if(this.cfgAutoTest)
         {
            this.fileLog("auto room id=" + loc.id + " " + this.spaceX + "x" + this.spaceY
               + " base=" + (loc.base || this.cfgBaseRooms[loc.id] == true)
               + " black=" + w.black + " mode=" + this.cfgMode
               + " enabled=" + this.cfgEnabled);
         }
      }

      /** 自建软雾层：低分辨率子格 + 模糊，插在 visLight 之后同一层级。
       *  不在这里隐藏 visLight（classic 模式需要原版掩膜；current 模式由
       *  applyVision 每帧隐藏）。 */
      private function ensureFog(w:World):void
      {
         if(w.grafon == null)
         {
            return;
         }
         if(this.fogVis == null)
         {
            this.fogVis = new Sprite();
            this.fogVis.mouseEnabled = false;
            this.fogVis.mouseChildren = false;
         }
         var bw:int = this.spaceX * FOG_SUB + FOG_PAD * 2;
         var bh:int = this.spaceY * FOG_SUB + FOG_PAD * 2;
         if(this.fogBmp == null || this.fogBmp.width != bw || this.fogBmp.height != bh)
         {
            if(this.fogBmp != null)
            {
               this.fogBmp.dispose();
            }
            if(this.fogRaw != null)
            {
               this.fogRaw.dispose();
            }
            if(this.fogCache != null)
            {
               this.fogCache.dispose();
            }
            this.fogRaw = new BitmapData(bw,bh,true,0xFF000000);
            this.fogCache = new BitmapData(bw,bh,true,0xFF000000);
            this.fogBmp = new BitmapData(bw,bh,true,0xFF000000);
            this.fogRect = new Rectangle(0,0,bw,bh);
            if(this.fogBitmap != null && this.fogBitmap.parent)
            {
               this.fogBitmap.parent.removeChild(this.fogBitmap);
            }
            this.fogBitmap = new Bitmap(this.fogBmp);
            // v0.22.1：**smoothing=true**（参考原版"模糊墙壁单位格子"思路——
            // 原版 lightBmp 1px/瓦片 + 双线性插值产生 40px 渐变雾带）。current
            // 的 5px 子格值之间双线性插值（5px 渐变带），消除 5px 像素块锯齿；
            // 配合 curBlur（4.0 ≈32px）→ 阴影边缘平滑柔和。线状阴影几何
            // （子格 raycast）保留，仅显示层插值。
            this.fogBitmap.smoothing = true;
            this.fogBitmap.scaleX = this.fogBitmap.scaleY = Tile.tileX / FOG_SUB;
            this.fogBitmap.x = this.fogBitmap.y = -FOG_PAD * Tile.tileX / FOG_SUB;
            this.fogVis.addChild(this.fogBitmap);
            this.fogDirty = true;
         }
         // classic（仿原版）v5 雾层：1px/瓦片，复刻原版 lightBmp——
         // ① smoothing=true 双线性插值（40px 值之间连续渐变 → 雾状感本体）
         // ② 半格错位（x=-tileX/2, y=-tileY/2-tileY，写 y+1 行——亮度像素
         //    中心落在瓦片西北角，墙亮面/暗边由错位自然产生，同原版）
         // ③ 尺寸 = (spaceX+1)×(spaceY+2)——**富余 1 列 2 行**（原版 lightBmp
         //    49×28 = 最大房间 48×26 + 同款富余）。无富余时错位后雾层右端
         //    缺 20px、底端缺 20px → 画面右下亮边缺口
         var cw:int = this.spaceX;
         var ch:int = this.spaceY;
         if(this.classicRaw == null || this.classicRaw.width != cw || this.classicRaw.height != ch)
         {
            if(this.classicRaw != null)
            {
               this.classicRaw.dispose();
            }
            if(this.classicBmp != null && this.classicBmp.parent)
            {
               this.classicBmp.parent.removeChild(this.classicBmp);
            }
            this.classicRaw = new BitmapData(cw,ch,true,0xFF000000); // 初始全黑
            this.classicBmp = new Bitmap(this.classicRaw,"auto",true); // smoothing=true
            this.classicBmp.scaleX = this.classicBmp.scaleY = Tile.tileX;
            // v0.23.3：**无错位**（x=0, y=0，像素对齐瓦片网格，写 (tx,ty)）
            // ——与墙专用层（同样无错位）同一坐标系。此前雾层是原版半格
            // 错位（x=-20/y=-60 写 y+1），墙层无错位——两套坐标导致雾层
            // 暗区（记忆区/未探索/光缘环）相对墙偏左上 20px（用户实测
            // "阴影明显向左上角错位"）
            this.classicBmp.x = 0;
            this.classicBmp.y = 0;
            this.fogVis.addChild(this.classicBmp);
            // 墙专用层（v0.25.4）：2px/瓦片、整层位移半格——每墙只写
            // (2x+1,2y+1) 单格（恰好覆盖整瓦片，见字段注释）
            var ww:int = this.spaceX * 2;
            var wh:int = this.spaceY * 2;
            if(this.wallRaw == null || this.wallRaw.width != ww || this.wallRaw.height != wh)
            {
               if(this.wallRaw != null)
               {
                  this.wallRaw.dispose();
               }
               if(this.wallBmp != null && this.wallBmp.parent)
               {
                  this.wallBmp.parent.removeChild(this.wallBmp);
               }
               this.wallRaw = new BitmapData(ww,wh,true,0); // 透明初始（不遮挡雾层）
               this.wallBmp = new Bitmap(this.wallRaw,"auto",true);
               this.wallBmp.scaleX = this.wallBmp.scaleY = Tile.tileX / 2;
               this.wallBmp.x = -Tile.tileX / 2;
               this.wallBmp.y = -Tile.tileY / 2;
               this.fogVis.addChild(this.wallBmp);   // classicBmp 之上
            }
            this.lastA = null;
         }
         if(this.lastA == null || this.lastA.length != this.spaceX * this.spaceY)
         {
            var nk:int = this.spaceX * this.spaceY;
            this.lastA = new Array(nk);
            this.memCur = new Array(nk);
            this.aArr = new Array(nk);
            this.wallKey = new Array(nk);
            var k:int;
            for(k = 0; k < nk; k++)
            {
               this.lastA[k] = -1;
               this.memCur[k] = 0;
               this.wallKey[k] = -1;   // 强制首帧全部写入
            }
         }
         // 模式可见性互斥：classic 显示 1px 雾层 + 墙层，current 显示 8×8 雾层
         var classicMode:Boolean = this.cfgMode == "classic";
         if(this.fogBitmap != null)
         {
            this.fogBitmap.visible = !classicMode;
         }
         if(this.classicBmp != null)
         {
            this.classicBmp.visible = classicMode;
         }
         if(this.wallBmp != null)
         {
            this.wallBmp.visible = classicMode;
         }
         var visual:Sprite = w.grafon.visual;
         if(this.fogVis.parent != visual)
         {
            var vi:int = visual.getChildIndex(w.grafon.visLight);
            visual.addChildAt(this.fogVis,vi + 1);
         }
         this.fogVis.visible = true;
         if(w.pers != null && (w.pers as Pers).infravis > 0)
         {
            this.fogVis.transform.colorTransform = this.infraCT;
            this.fogVis.blendMode = "multiply";
         }
         else
         {
            this.fogVis.transform.colorTransform = this.defCT;
            this.fogVis.blendMode = "normal";
         }
      }

      /** 透传模式（原版）：停用模组雾层，visi/visLight/lightBmp 完全交还游戏。
       *  进入透传瞬间用 setLight() 把掩膜恢复到当前 visi 状态（模式切换后
       *  lightBmp 可能残留模组活动期的旧值；房间进入时 drawLoc 已调过，
       *  重复调用无害）。 */
      private function normalMode(w:World, loc:Location):void
      {
         if(this.fogVis != null)
         {
            this.fogVis.visible = false;
         }
         if(!this.normalApplied)
         {
            this.normalApplied = true;
            if(w.grafon != null)
            {
               try
               {
                  w.grafon.setLight();
                  w.grafon.visLight.visible = loc.black && w.black;
               }
               catch(err:Error)
               {
               }
            }
         }
      }

      /** 透传路径（vanilla / 总开关关 / 安全基地）恢复全部残留（v0.24.6）：
       *  ① 摘除全部掩膜（含残留在显示树中的掩膜 Shape，过期掩膜会继续裁剪
       *     单位 → 原版"隐身敌人"）；② 恢复被隐藏单位的 vis/prior/hpbar；
       *  ③ 恢复敌方武器（visible + 摘 mask + 关 cacheAsBitmap）；④ 恢复
       *  显示树中被隐藏的附属对象（狮鹫手臂等）。门控：无残留时零开销。 */
      private function restoreAll(w:World, loc:Location):void
      {
         var any:Boolean = false;
         for(var k:Object in this.unitVis) { any = true; break; }
         if(!any)
         {
            for(var kh:Object in this.hpHidden) { any = true; break; }
         }
         if(!any)
         {
            for(var km:Object in this.managedHidden) { any = true; break; }
         }
         if(!any)
         {
            return;
         }
         for(var ku:Object in this.unitVis)
         {
            var u:Unit = ku as Unit;
            if(u != null)
            {
               this.clearMask(u);
            }
         }
         this.unitVis = new Dictionary(true);
         for(var khu:Object in this.hpHidden)
         {
            var uh:Unit = khu as Unit;
            if(uh != null)
            {
               this.showUnit(uh);
            }
         }
         this.hpHidden = new Dictionary(true);
         var obj:Pt = loc.firstObj;
         var guard:int = 0;
         while(obj != null && guard < 5000)
         {
            if(obj is Weapon)
            {
               this.setWeaponVis(obj as Weapon,true);
            }
            obj = obj.nobj;
            guard++;
         }
         for(var md:Object in this.managedHidden)
         {
            var c:DisplayObject = md as DisplayObject;
            if(c != null)
            {
               c.visible = true;
            }
         }
         this.managedHidden = new Dictionary(true);
         this.managedCount = 0;
      }

      /** 阻挡结构哈希：opac>0 / phis>0 逐瓦片累计（用于墙破坏/开门/关门的即时检测）。 */
      private function structHash(loc:Location):int
      {
         var h:int = 0;
         var tx:int;
         var ty:int;
         for(tx = 0; tx < this.spaceX; tx++)
         {
            for(ty = 0; ty < this.spaceY; ty++)
            {
               var t:Tile = loc.getTile(tx,ty);
               h = h * 31 + (t.opac > 0 ? 1 : 0) + (t.phis > 0 ? 2 : 0);
            }
         }
         return h;
      }

      /** 悬停在不可见敌人上时清除 celObj（杀名称标签，与游戏 getDist 同机制）。 */
      private function blockInvisibleHover(loc:Location, gg:UnitPlayer):void
      {
         var co:Object = loc.celObj;
         if(co == null || !(co is Unit))
         {
            return;
         }
         var cu:Unit = co as Unit;
         if(cu.player || cu.npc || cu.fraction == Unit.F_PLAYER)
         {
            return;
         }
         if(this.enemyState(loc,cu) == 0)
         {
            loc.celObj = null;
         }
      }

      // ==================== FOV ====================

      private function computeFov(loc:Location):void
      {
         var gg:UnitPlayer = loc.gg;
         var ex:Number = gg.X;
         var ey:Number = gg.Y - gg.scY * 0.75;
         this.eyeX = ex;
         this.eyeY = ey;
         var r:Number = loc.lDist2;
         if(r < Tile.tileX)
         {
            r = Tile.tileX;
         }
         var r2:Number = r * r;
         var tx:int;
         var ty:int;
         for(tx = 0; tx < this.spaceX; tx++)
         {
            for(ty = 0; ty < this.spaceY; ty++)
            {
               var i:int = tx + ty * this.spaceX;
               var cx:Number = (tx + 0.5) * Tile.tileX;
               var cy:Number = (ty + 0.5) * Tile.tileY;
               var dx:Number = cx - ex;
               var dy:Number = cy - ey;
               if(dx * dx + dy * dy > r2)
               {
                  this.fov[i] = FOV_NONE;
                  continue;
               }
               var lit:Number = this.castRay(loc,ex,ey,cx,cy,tx,ty);
               // 连续亮度（原版渐变）：LOS 亮度 × 距离衰减
               var distF:Number = this.distFalloff(dx * dx + dy * dy);
               var b:Number = lit < 0 ? 0 : lit * distF;
               if(b > 1)
               {
                  b = 1;
               }
               this.br[i] = b;
               this.litArr[i] = lit < 0 ? 0 : (lit > 1 ? 1 : lit);
               if(lit >= this.cfgLitMin)
               {
                  this.fov[i] = FOV_VISIBLE;
                  this.explored[i] = 1;
               }
               else if(lit > 0.0001)
               {
                  this.fov[i] = FOV_DIM;
                  this.explored[i] = 1;
               }
               else
               {
                  this.fov[i] = FOV_NONE;
               }
            }
         }
         // 墙可见性：只由"可见的非阻挡瓦片"点亮，不链式传播（厚墙内部保持暗）
         for(tx = 0; tx < this.spaceX; tx++)
         {
            for(ty = 0; ty < this.spaceY; ty++)
            {
               var j:int = tx + ty * this.spaceX;
               if(this.fov[j] == FOV_VISIBLE)
               {
                  continue;
               }
               var t:Tile = loc.getTile(tx,ty);
               if(t.opac <= 0)
               {
                  continue;
               }
               for each(var nb:Array in WALL_NEIGHBORS)
               {
                  var nx:int = tx + nb[0];
                  var ny:int = ty + nb[1];
                  if(nx >= 0 && nx < this.spaceX && ny >= 0 && ny < this.spaceY)
                  {
                     var ni:int = nx + ny * this.spaceX;
                     if(this.fov[ni] == FOV_VISIBLE && loc.getTile(nx,ny).opac <= 0)
                     {
                        this.fov[j] = FOV_VISIBLE;
                        this.explored[j] = 1;
                        // 墙瓦片按距离衰减取连续亮度（墙的亮面随光缘渐变）
                        var wdx:Number = (tx + 0.5) * Tile.tileX - ex;
                        var wdy:Number = (ty + 0.5) * Tile.tileY - ey;
                        this.br[j] = this.distFalloff(wdx * wdx + wdy * wdy);
                        this.litArr[j] = 1;
                        break;
                     }
                  }
               }
            }
         }
      }

   private function castRay(loc:Location, ex:Number, ey:Number, cx:Number, cy:Number, tx:int, ty:int):Number
      {
         var lit:Number = 1;
         var leaked:Boolean = false;
         var dx:Number = cx - ex;
         var dy:Number = cy - ey;
         var c0x:int = Math.floor(ex / Tile.tileX);
         var c0y:int = Math.floor(ey / Tile.tileY);
         var stepX:int;
         var stepY:int;
         var tMaxX:Number;
         var tMaxY:Number;
         var tDeltaX:Number;
         var tDeltaY:Number;
         if(dx > 0)
         {
            stepX = 1;
            tMaxX = ((c0x + 1) * Tile.tileX - ex) / dx;
            tDeltaX = Tile.tileX / dx;
         }
         else if(dx < 0)
         {
            stepX = -1;
            tMaxX = (c0x * Tile.tileX - ex) / dx;
            tDeltaX = -Tile.tileX / dx;
         }
         else
         {
            stepX = 0;
            tMaxX = Number.POSITIVE_INFINITY;
            tDeltaX = 0;
         }
         if(dy > 0)
         {
            stepY = 1;
            tMaxY = ((c0y + 1) * Tile.tileY - ey) / dy;
            tDeltaY = Tile.tileY / dy;
         }
         else if(dy < 0)
         {
            stepY = -1;
            tMaxY = (c0y * Tile.tileY - ey) / dy;
            tDeltaY = -Tile.tileY / dy;
         }
         else
         {
            stepY = 0;
            tMaxY = Number.POSITIVE_INFINITY;
            tDeltaY = 0;
         }
         var c1x:int = c0x;
         var c1y:int = c0y;
         var guard:int = 0;
         var t:Tile;
         var op:Number;
         while(c1x != tx || c1y != ty)
         {
            if(++guard > 400)
            {
               break;
            }
            if(tMaxX < tMaxY)
            {
               tMaxX += tDeltaX;
               c1x += stepX;
            }
            else
            {
               tMaxY += tDeltaY;
               c1y += stepY;
            }
            t = loc.getTile(c1x,c1y);
            op = this.tileOpac(loc,t);
            // 全实心（墙/金属门）→ 完全阻挡；部分透光（木门/栅格/水）→ 泄漏暗色视野
            if(op >= 1)
            {
               return -1;
            }
            if(op > 0)
            {
               leaked = true;
            }
            lit -= op;
         }
         t = loc.getTile(tx,ty);
         op = this.tileOpac(loc,t);
         if(op >= 1)
         {
            return -1;
         }
         if(op > 0)
         {
            leaked = true;
         }
         lit -= op;
         if(lit < 0)
         {
            lit = 0;
         }
         if(lit > 1)
         {
            lit = 1;
         }
         // 多层部分透光叠加（斜穿双格宽木门等）仍提供暗色视野
         if(leaked && lit < 0.0001)
         {
            return 0.05;
         }
         return lit;
      }

      private function tileOpac(loc:Location, t:Tile):Number
      {
         var op:Number = t.opac;
         if(loc.opacWater > 0 && t.water > 0 && loc.opacWater > op)
         {
            op = loc.opacWater;
         }
         return op;
      }

      /** 三态写入 visi/t_visi + 软雾图（脏标记门控：无变化整帧跳过）。 */
      /**
       * current（真实线状 + 渐变过渡）：阴影边界由光线几何产生——对已探索瓦片
       * 的每个子格（5px）中心独立 castRay，亮度 = max(lit × 距离衰减, 记忆暗色)。
       * 边界瓦片内部不同子格光线路径不同 → 线状阴影；随后施加模糊
       * （2.5px 子格 ≈ 20px 世界）→ 阴影边缘渐变过渡（软阴影）。
       *
       * 性能（v0.17.1）：最终 alpha 场缓存在 fogCache，只在 FOV 重算时更新；
       * 重算时每瓦片先做 4 角采样分类——全暗（记忆区）整块 fillRect、全亮
       * （视野内）无 raycast 只算距离衰减、只有边界/泄漏瓦片（角点明暗混合或
       * FOV_DIM）才做完整 8×8 raycast。站立时（淡入帧）零 raycast。
       */
      private function applyVision(w:World, loc:Location, needFov:Boolean):void
      {
         this.ensureFog(w);
         // v0.24.7：模糊+钳制拆到 fov 帧的下一帧执行——fov 帧峰值从
         // ~3ms 降到 ~1.7ms（模糊 0.3 + 钳制 ~1ms 移到次帧；显示滞后 1 帧
         // 不可察觉）。门控：无变化且无待办模糊时整帧跳过
         if(this.fogBmp == null || (!this.fogDirty && !this.fogBlurPending))
         {
            return;
         }
         if(w.grafon != null)
         {
            w.grafon.visLight.visible = false;
         }
         var fieldFresh:Boolean = false;
         if(needFov)
         {
            this.fillFogCache(loc);
            this.fogBlurPending = true;
            if(this.cfgAutoTest)
            {
               this.atBlurD++;
            }
            fieldFresh = true;
         }
         var changed:Boolean = false;
         var fading:Boolean = false;
         var tx:int;
         var ty:int;
         if(this.fogDirty)
         {
            for(tx = 0; tx < this.spaceX; tx++)
            {
               for(ty = 0; ty < this.spaceY; ty++)
               {
                  var i:int = tx + ty * this.spaceX;
                  var gv:Number = this.explored[i] == 1 ? 1 : 0;
                  // 淡入进度（进房/开关时 0→1；收敛后子格值即最终亮度）
                  var cur:Number = this.visCur[i];
                  if(cur < 1)
                  {
                     cur += this.cfgFadeStep;
                     if(cur > 1)
                     {
                        cur = 1;
                     }
                     this.visCur[i] = cur;
                     changed = true;
                     if(cur < 1)
                     {
                        fading = true;
                     }
                  }
                  var t:Tile = loc.getTile(tx,ty);
                  // 只写 visi（二元，供 checkPort/地图/Sats 等游戏逻辑），
                  // 不写 t_visi（v0.21.1）：t_visi 保留游戏 lighting() 的目标值，
                  // 退出 current 后游戏可自愈恢复（见 resetRoom 注释）
                  t.visi = gv;
               }
            }
            if(fading)
            {
               // 淡入帧：fogRaw = 按每瓦片 cur 缩放缓存场（alpha = 255 - cur×(255-cacheA)）
               this.fogRaw.lock();
               for(tx = 0; tx < this.spaceX; tx++)
               {
                  for(ty = 0; ty < this.spaceY; ty++)
                  {
                     var cf:Number = this.visCur[tx + ty * this.spaceX];
                     var px0:int = FOG_PAD + tx * FOG_SUB;
                     var py0:int = FOG_PAD + ty * FOG_SUB;
                     if(cf >= 1)
                     {
                        this.fogCellRect.x = px0;
                        this.fogCellRect.y = py0;
                        this.fogCellPoint.x = px0;
                        this.fogCellPoint.y = py0;
                        this.fogRaw.copyPixels(this.fogCache,this.fogCellRect,this.fogCellPoint);
                     }
                     else
                     {
                        var sx:int;
                        var sy:int;
                        for(sx = 0; sx < FOG_SUB; sx++)
                        {
                           for(sy = 0; sy < FOG_SUB; sy++)
                           {
                              var ca:int = this.fogCache.getPixel32(px0 + sx,py0 + sy) >>> 24;
                              var a:int = 255 - cf * (255 - ca);
                              if(a < 0)
                              {
                                 a = 0;
                              }
                              else if(a > 255)
                              {
                                 a = 255;
                              }
                              this.fogRaw.setPixel32(px0 + sx,py0 + sy,a << 24);
                           }
                        }
                     }
                  }
               }
               this.fogRaw.unlock();
            }
            else
            {
               // 收敛后：缓存场直接拷贝（无逐像素循环）
               this.fogRaw.copyPixels(this.fogCache,this.fogRect,this.fogPoint);
            }
         }
         if(this.fogBlurPending && !fieldFresh)
         {
            // 模糊 → 阴影边缘渐变过渡（source≠dest）
            this.fogBmp.applyFilter(this.fogRaw,this.fogRect,this.fogPoint,this.curBlur);
            // 单侧钳制（D16）：display = max(raw, blurred)——暗区/未探索/墙保持洁净，
            // 只允许暗色向亮区渐变（窗户/亮面的光晕不向黑墙渗透）。
            // v0.24.5：逐像素 getPixel32/setPixel32（fov 重算卡顿主要来源）→
            // getVector/setVector 整块拷贝 + 纯内存比较（alpha 即 uint 高位，
            // 像素恒黑可直接比较）
            var vRaw:Vector.<uint> = this.fogRaw.getVector(this.fogRect);
            var vBlur:Vector.<uint> = this.fogBmp.getVector(this.fogRect);
            var np:int = vRaw.length;
            for(var vi:int = 0; vi < np; vi++)
            {
               if(vBlur[vi] < vRaw[vi])
               {
                  vBlur[vi] = vRaw[vi];
               }
            }
            this.fogBmp.setVector(this.fogRect,vBlur);
            this.fogBlurPending = false;
         }
         if(!changed)
         {
            this.fogDirty = false;
         }
      }

      /** current：最终 alpha 场写入 fogCache（仅 FOV 重算时调用）。 */
      private function fillFogCache(loc:Location):void
      {
         var dimF:Number = this.cfgDim;
         var dimA:int = Math.round((1 - dimF) * 255);
         var doorF:Number = this.cfgDoorDim;
         var d2max:Number = this.locDist2 * this.locDist2;
         var cs:Number = Tile.tileX / FOG_SUB;
         this.fogCache.lock();
         var tx:int;
         var ty:int;
         for(tx = 0; tx < this.spaceX; tx++)
         {
            for(ty = 0; ty < this.spaceY; ty++)
            {
               var i:int = tx + ty * this.spaceX;
               var bx:Number = tx * Tile.tileX;
               var by:Number = ty * Tile.tileY;
               var f:int = this.fov[i];
               var t:Tile = loc.getTile(tx,ty);
               if(f == FOV_DIM)
               {
                  // 透光门/水后：门景亮度（doordim，比记忆暗色亮），逐子格重算
                  this.recalcTile(loc,tx,ty,bx,by,doorF,dimA,cs,true);
                  continue;
               }
               if(f == FOV_VISIBLE && t.opac >= 1)
               {
                  // 可见墙（邻域点亮规则）：复刻原版"掩膜半格错位 → 墙内一定厚度
                  // 为亮区"——面向亮区邻域的半个瓦片按邻域亮度点亮，背侧保持
                  // 暗色/黑；墙在光缘处的亮度随邻域衰减
                  this.fillWallTile(loc,tx,ty,bx,by,cs);
                  continue;
               }
               // 4 角采样分类：全暗→记忆区/未探索整块；全亮→无 raycast 距离衰减；
               // 明暗混合→边界瓦片完整 8×8 重算（线状阴影由这些瓦片产生）
               var cLit:int = 0;
               var sx:int;
               var sy:int;
               for(sx = 0; sx < 2; sx++)
               {
                  for(sy = 0; sy < 2; sy++)
                  {
                     var subX:Number = bx + CORNER_OFFS_X[sx] * cs;
                     var subY:Number = by + CORNER_OFFS_Y[sy] * cs;
                     var dx:Number = subX - this.eyeX;
                     var dy:Number = subY - this.eyeY;
                     var lit:Number = dx * dx + dy * dy <= d2max
                        ? this.castRay(loc,this.eyeX,this.eyeY,subX,subY,
                           Math.floor(subX / Tile.tileX),Math.floor(subY / Tile.tileY))
                        : -1;
                     if(lit > 0.0001)
                     {
                        cLit++;
                        // 可见角 → 子格"曾见"历史（记忆区↔未探索边界 5px 粒度；
                        // 已探索瓦片同样标记，否则记忆区填充会出黑斑）
                        this.seenSub[(ty * FOG_SUB + sy) * this.subW + (tx * FOG_SUB + sx)] = 1;
                     }
                  }
               }
               if(f == FOV_VISIBLE && cLit == 4)
               {
                  // 全亮瓦片：无 raycast，逐子格距离衰减（含记忆暗色下限）
                  this.fillLitTile(tx,ty,bx,by,dimF,cs);
               }
               else if(cLit == 0)
               {
                  // 全暗瓦片（记忆区/未探索）：按子格"曾见"历史填充——曾见→记忆
                  // 暗色，从未见→黑。已探索瓦片不再整块 166（v0.17.4 回归的
                  // 40px 阶梯）：记忆区边界由子格历史形状决定（5px 粒度）
                  this.fillMemoryTile(tx,ty,dimA);
               }
               else
               {
                  // 边界瓦片（含阴影线/泄漏/曾见边缘）：完整 8×8 raycast
                  this.recalcTile(loc,tx,ty,bx,by,dimF,dimA,cs,false);
               }
            }
         }
         this.fogCache.unlock();
      }

      /**
       * 边界瓦片完整 8×8 子格 raycast。
       * doorView=true：透光门/水后——所有子格用门景亮度（floor=doordim）；
       * 否则：亮子格 max(lit×falloff, floor)，暗子格=曾见→记忆暗色，否则黑。
       * 当前可见子格一律记入"曾见"历史（含 doorView 与已探索瓦片——记忆区
       * 填充按子格历史，漏标会出现黑斑）。
       */
      private function recalcTile(loc:Location, tx:int, ty:int, bx:Number, by:Number,
         floorF:Number, dimA:int, cs:Number, doorView:Boolean):void
      {
         var sx:int;
         var sy:int;
         for(sx = 0; sx < FOG_SUB; sx++)
         {
            for(sy = 0; sy < FOG_SUB; sy++)
            {
               var subX:Number = bx + (sx + 0.5) * cs;
               var subY:Number = by + (sy + 0.5) * cs;
               var sdx:Number = subX - this.eyeX;
               var sdy:Number = subY - this.eyeY;
               var lit:Number = this.castRay(loc,this.eyeX,this.eyeY,subX,subY,
                  Math.floor(subX / Tile.tileX),Math.floor(subY / Tile.tileY));
               if(lit < 0)
               {
                  lit = 0;
               }
               else if(lit > 1)
               {
                  lit = 1;
               }
               if(lit > 0.0001)
               {
                  this.seenSub[(ty * FOG_SUB + sy) * this.subW + (tx * FOG_SUB + sx)] = 1;
               }
               var a:int;
               if(doorView)
               {
                  var br:Number = lit * this.distFalloff(sdx * sdx + sdy * sdy);
                  if(br < floorF)
                  {
                     br = floorF;
                  }
                  a = Math.round((1 - br) * 255);
               }
               else if(lit > 0.0001)
               {
                  br = lit * this.distFalloff(sdx * sdx + sdy * sdy);
                  if(br < floorF)
                  {
                     br = floorF;
                  }
                  a = Math.round((1 - br) * 255);
               }
               else if(this.seenSub[(ty * FOG_SUB + sy) * this.subW + (tx * FOG_SUB + sx)] == 1)
               {
                  a = dimA;
               }
               else
               {
                  a = 255;
               }
               this.fogCache.setPixel32(FOG_PAD + tx * FOG_SUB + sx,FOG_PAD + ty * FOG_SUB + sy,a << 24);
            }
         }
      }

      /** current：全亮瓦片无 raycast 填充——逐子格距离衰减（亮度 = max(falloff, dim)）。
       *  4 角已确认全在视野半径内（角是瓦片最远点）→ 整瓦片记入"曾见"历史
       *  （记忆区按子格历史填充，漏标会出现黑斑）。 */
      private function fillLitTile(tx:int, ty:int, bx:Number, by:Number, dimF:Number, cs:Number):void
      {
         var idxBase:int = ty * FOG_SUB * this.subW + tx * FOG_SUB;
         var sx:int;
         var sy:int;
         for(sx = 0; sx < FOG_SUB; sx++)
         {
            for(sy = 0; sy < FOG_SUB; sy++)
            {
               this.seenSub[idxBase + sy * this.subW + sx] = 1;
            }
         }
         for(sx = 0; sx < FOG_SUB; sx++)
         {
            for(sy = 0; sy < FOG_SUB; sy++)
            {
               var subX:Number = bx + (sx + 0.5) * cs;
               var subY:Number = by + (sy + 0.5) * cs;
               var dx:Number = subX - this.eyeX;
               var dy:Number = subY - this.eyeY;
               var f:Number = this.distFalloff(dx * dx + dy * dy);
               if(f < dimF)
               {
                  f = dimF;
               }
               this.fogCache.setPixel32(FOG_PAD + tx * FOG_SUB + sx,FOG_PAD + ty * FOG_SUB + sy,
                  Math.round((1 - f) * 255) << 24);
            }
         }
      }

      /**
       * current：可见墙瓦片（opac≥1，邻域点亮规则）——复刻原版"掩膜半格错位 →
       * 墙内一定厚度为亮区"：四分格映射（TL=自身 / TR=东 / BL=南 / BR=东南），
       * 每格显示其对应瓦片的连续亮度 br（光滑场，无逐瓦片马赛克波痕）；
       * 对应瓦片为墙/暗区时按历史（曾见→记忆暗色，否则→黑）。
       */
      private function fillWallTile(loc:Location, tx:int, ty:int, bx:Number, by:Number, cs:Number):void
      {
         var dimF:Number = this.cfgDim;
         var dimA:int = Math.round((1 - dimF) * 255);
         var half:int = FOG_SUB / 2;
         var idxBase:int = ty * FOG_SUB * this.subW + tx * FOG_SUB;
         var sx:int;
         var sy:int;
         for(sx = 0; sx < FOG_SUB; sx++)
         {
            for(sy = 0; sy < FOG_SUB; sy++)
            {
               var nx:int = tx + (sx >= half ? 1 : 0);
               var ny:int = ty + (sy >= half ? 1 : 0);
               var a:int;
               if(nx < this.spaceX && ny < this.spaceY)
               {
                  var ni:int = nx + ny * this.spaceX;
                  var nf:int = this.fov[ni];
                  if(nf != FOV_NONE)
                  {
                     var b:Number = this.br[ni];
                     if(b < dimF)
                     {
                        b = dimF;
                     }
                     a = Math.round((1 - b) * 255);
                     this.seenSub[idxBase + sy * this.subW + sx] = 1;
                  }
                  else if(this.explored[ni] == 1)
                  {
                     a = dimA;
                     this.seenSub[idxBase + sy * this.subW + sx] = 1;
                  }
                  else
                  {
                     a = 255;
                  }
               }
               else
               {
                  a = 255;
               }
               this.fogCache.setPixel32(FOG_PAD + tx * FOG_SUB + sx,FOG_PAD + ty * FOG_SUB + sy,a << 24);
            }
         }
      }

      /**
       * 全暗瓦片（记忆区/未探索）按子格"曾见"历史填充：曾见→记忆暗色 dimA，
       * 从未见→全黑。快路径：整块已见→fillRect(dimA)，整块未见→fillRect(黑)。
       * 记忆区边界由 seenSub 形状决定（5px 粒度），不再整块 40px 阶梯。
       */
      private function fillMemoryTile(tx:int, ty:int, dimA:int):void
      {
         var idxBase:int = ty * FOG_SUB * this.subW + tx * FOG_SUB;
         var seenAll:Boolean = true;
         var seenAny:Boolean = false;
         var sx:int;
         var sy:int;
         for(sx = 0; sx < FOG_SUB; sx++)
         {
            for(sy = 0; sy < FOG_SUB; sy++)
            {
               if(this.seenSub[idxBase + sy * this.subW + sx] == 1)
               {
                  seenAny = true;
               }
               else
               {
                  seenAll = false;
               }
            }
         }
         this.fogCellRect.x = FOG_PAD + tx * FOG_SUB;
         this.fogCellRect.y = FOG_PAD + ty * FOG_SUB;
         if(seenAll)
         {
            // 整块都曾见（记忆区内部）：均匀暗色
            this.fogCache.fillRect(this.fogCellRect,dimA << 24);
            return;
         }
         if(!seenAny)
         {
            // 从未见过（未探索内部）：整块全黑
            this.fogCache.fillRect(this.fogCellRect,0xFF000000);
            return;
         }
         var px0:int = FOG_PAD + tx * FOG_SUB;
         var py0:int = FOG_PAD + ty * FOG_SUB;
         for(sx = 0; sx < FOG_SUB; sx++)
         {
            for(sy = 0; sy < FOG_SUB; sy++)
            {
               this.fogCache.setPixel32(px0 + sx,py0 + sy,
                  (this.seenSub[idxBase + sy * this.subW + sx] == 1 ? dimA : 255) << 24);
            }
         }
      }

      /**
       * classic（仿原版）v6：**游戏值优先**——复刻原版光照管线（原版雾状感），
       * 唯一的模组干预是记忆区亮度下限。
       *
       * 原版"雾"的三要素（反编译确认）：
       * ① lightBmp 是 1px/瓦片 的 alpha 遮罩 + Bitmap smoothing=true（双线性
       *    插值）——40px 瓦片值之间连续渐变，边界是柔和的雾带而非硬块；
       * ② 半格错位（visLight.x=-tileX/2、y=-tileY/2-tileY，写入 y+1 行）——
       *    每个瓦片的亮度像素中心落在瓦片西北角，墙的亮面/暗边由错位自然
       *    产生（东/南邻值渗入墙内半格，原版同款）；
       * ③ visi 渐进节奏——Tile.updVisi() 每帧 +0.1 向 t_visi 逼近（淡入），
       *    lighting() 后 10 帧 lighting2() 持续刷新（雾"呼吸"），retDark 房间
       *    变暗目标每帧 -0.025（雾消退尾迹）。
       * ④ 距离衰减环（lDist1=300 全亮 → lDist2=1000 线性降暗到 0）是原版
       *    边界的本体；墙永远不被游戏点亮（walk 末步检查目标瓦片 opac），
       *    原版墙恒黑、仅靠错位渗入邻瓦亮值。
       *
       * v6 规则（每帧读游戏 tile.visi，1px/瓦片写 classicRaw，y+1 错位）：
       *   a = (1-visi)×255  —— 游戏值原样：视野内衰减环梯度/淡入节奏/
       *     retDark 消退/光源物/门景/墙恒黑+错位渗亮，全部与 vanilla 相同；
       *   仅当（非 retDark && 非墙 && 当前视野外 && a < dimA）：
       *     a = dimA  —— 记忆区下限：内部（visi≈1）均匀 166；边界瓦片
       *     （游戏距离衰减冻结值 0~0.35）保留游戏衰减梯度（166 渐变到黑，
       *     原版风格边界，无亮步/无块状）。
       * 变化才写像素（lastA 缓存）；边缘行列照抄原版（lighting 循环从 1 开始，
       * 恒定黑）。站立时游戏 visi 冻结 → 零写入。
       */
      private function applyVisionClassic(w:World, loc:Location, needFov:Boolean):void
      {
         // v0.24.7：30Hz 门控——偶数帧或 fov 变化帧才跑全图循环。站立时游戏
         // visi 冻结（循环零写入）；移动时游戏 visi 自身 +0.1/帧平滑渐变，
         // 30Hz 采样不可察觉；memCur 渐变速率随之减半，同样不可察觉
         if((this.frameCount & 1) != 0 && !needFov)
         {
            if(this.cfgAutoTest)
            {
               this.atClsS++;
            }
            return;
         }
         if(this.cfgAutoTest)
         {
            this.atClsF++;
         }
         this.ensureFog(w);
         if(this.classicRaw == null)
         {
            return;
         }
         if(w.grafon != null)
         {
            w.grafon.visLight.visible = false;
         }
         var dimF:Number = this.cfgDim;
         var dimA:int = Math.round((1 - dimF) * 255);
         var retDark:Boolean = loc.retDark == true;
         var tx:int;
         var ty:int;
         // 写入范围：全图（v0.23.3 无错位——像素 (tx,ty) 对齐瓦片网格，
         // 不再照抄原版的"写 y+1 行 + 半格错位"（错位与墙层坐标系不一致））
         for(ty = 0; ty < this.spaceY; ty++)
         {
            for(tx = 0; tx < this.spaceX; tx++)
            {
               var i:int = tx + ty * this.spaceX;
               var t:Tile = loc.getTile(tx,ty);
               var gv:Number = t.visi;
               if(gv < 0)
               {
                  gv = 0;
               }
               else if(gv > 1)
               {
                  gv = 1;
               }
               // 游戏值（原版渲染原样：视野内衰减环梯度 / 淡入节奏 /
               // retDark 消退 / 光源物 / 门景 / 墙恒黑+半格错位渗亮）
               var gameA:int = Math.round((1 - gv) * 255);
               // 记忆化进度（0.1/帧，与原版 visi 渐入同款节奏）：视野外渐增、
               // 视野内渐减——移动时记忆区边界平滑渐变（消灭 fov 瓦片级二值
               // 切换的"格子感"），收敛后与 v6 规则一致
               var mem:Boolean = !retDark && this.fov[i] == FOV_NONE;
               var cur:Number = this.memCur[i];
               if(mem)
               {
                  cur += this.cfgFadeStep;
                  if(cur > 1)
                  {
                     cur = 1;
                  }
               }
               else
               {
                  cur -= this.cfgFadeStep;
                  if(cur < 0)
                  {
                     cur = 0;
                  }
               }
               this.memCur[i] = cur;
               // v0.24.9：墙与地板同公式——原版 lighting() 对墙无特判：
               // 射线终点（墙瓦片）自身 opac 不被扣减，可达墙面 t_visi≈1，
               // 未探索墙 visi=0 保持黑。mem 记忆混合不再排除墙
               // v0.25.5：记忆目标统一 dimA（对齐 current 的 fillMemoryTile
               // 语义：已探索=统一记忆暗色）。原 max(gameA, dimA) 会让弱照明
               // 瓦片（gameA>dimA——游戏 visi 场本就斑驳，墙的转角射线尤甚）
               // 保持暗斑不参与调暗 = 记忆区脏迹（用户截图实测对比 current）
               var memT:int = this.explored[i] == 1 ? dimA : 255;
               var a:int = Math.round(gameA + cur * (memT - gameA));
               this.aArr[i] = a;
               if(t.opac >= 1)
               {
                  this.lastA[i] = a;   // 占位，第二遍协调值不同会重写
               }
               else if(a != this.lastA[i])
               {
                  this.lastA[i] = a;
                  this.classicRaw.setPixel32(tx,ty,a << 24);
               }
            }
         }
         // 第二遍（v0.25.2）：① 雾层墙像素=邻域协调值（4 邻非墙 aArr 平均
         // ——邻瓦靠墙处保持其遮罩值，无稀释；全墙邻兜底=自身值）；
         // ② 墙专用层写自身公式值单值（层位移半格，wallKey 门控——站立零写）
         if(this.wallRaw != null)
         {
            this.wallRaw.lock();
            this.classicRaw.lock();
            for(ty = 0; ty < this.spaceY; ty++)
            {
               for(tx = 0; tx < this.spaceX; tx++)
               {
                  var wi:int = tx + ty * this.spaceX;
                  var key:int;
                  if(loc.getTile(tx,ty).opac >= 1)
                  {
                     // ① 雾层墙像素：邻域协调值（4 邻非墙 aArr 平均，越界跳过）
                     var ssum:int = 0;
                     var scnt:int = 0;
                     if(ty > 0 && loc.getTile(tx,ty - 1).opac < 1)
                     {
                        ssum += this.aArr[tx + (ty - 1) * this.spaceX];
                        scnt++;
                     }
                     if(ty + 1 < this.spaceY && loc.getTile(tx,ty + 1).opac < 1)
                     {
                        ssum += this.aArr[tx + (ty + 1) * this.spaceX];
                        scnt++;
                     }
                     if(tx > 0 && loc.getTile(tx - 1,ty).opac < 1)
                     {
                        ssum += this.aArr[(tx - 1) + ty * this.spaceX];
                        scnt++;
                     }
                     if(tx + 1 < this.spaceX && loc.getTile(tx + 1,ty).opac < 1)
                     {
                        ssum += this.aArr[(tx + 1) + ty * this.spaceX];
                        scnt++;
                     }
                     // ① 雾层墙像素：邻域协调值（4 邻非墙 aArr 平均，越界跳过；
                     // 全墙邻兜底=自身值）——全部墙统一，地板侧无稀释无亮带
                     var awall:int = scnt > 0 ? Math.round(ssum / scnt) : this.aArr[wi];
                     if(awall != this.lastA[wi])
                     {
                        this.lastA[wi] = awall;
                        this.classicRaw.setPixel32(tx,ty,awall << 24);
                     }
                     // ② 墙层：写自身公式值单值（4 子格同值）。层位移半格后
                     // 值块覆盖墙 NW 半格，墙 SE 半格露出雾层协调值（≈邻域
                     // 地板亮度）——阴影 50% 线落在瓦片中线（原版位置），
                     // 单值干净无拼块
                     key = this.aArr[wi] & 0xFF;
                  }
                  else
                  {
                     key = 0;   // 墙层透明（不遮挡雾层）
                  }
                  if(key != this.wallKey[wi])
                  {
                     this.wallKey[wi] = key;
                     // v0.25.4：只写 (2tx+1,2ty+1) 一格——层位移 (-20,-20) 下
                     // 该格恰好精确覆盖整块墙瓦片、零溢出；v0.25.2/3 的 4 格
                     // 写法含 (2tx,·)/(·,2ty) 的 W/N 溢出格，把墙自身值画进
                     // 邻地板 20px = 屏幕边缘亮带与墙旁脏迹的来源（离线像素
                     // 模拟 rv0253-wall-smudge-sim2.py 四版对比确认）
                     this.wallRaw.setPixel32(2 * tx + 1, 2 * ty + 1, key << 24);
                  }
               }
            }
            this.classicRaw.unlock();
            this.wallRaw.unlock();
         }
      }

      /**
       * classic：透光门/水后的门景亮度提升——fov==DIM 瓦片把 visi 抬到 doordim
       * （比记忆暗色亮），雾场直接读取该 visi。游戏 lighting() 只升不降且计算
       * 的透过亮度 < doordim，不会覆盖。
       */
      private function doorBoost(w:World, loc:Location):void
      {
         var tx:int;
         var ty:int;
         for(tx = 0; tx < this.spaceX; tx++)
         {
            for(ty = 0; ty < this.spaceY; ty++)
            {
               if(this.fov[tx + ty * this.spaceX] == FOV_DIM)
               {
                  var t:Tile = loc.getTile(tx,ty);
                  t.visi = this.cfgDoorDim;
                  t.t_visi = this.cfgDoorDim;
               }
            }
         }
      }

      /** 距离衰减因子：全亮半径内 1，向外到视野半径线性降到 0（原版 lDist1→lDist2）。 */
      private function distFalloff(d2:Number):Number
      {
         var d:Number = Math.sqrt(d2);
         if(d <= this.locDist1)
         {
            return 1;
         }
         if(d >= this.locDist2)
         {
            return 0;
         }
         return (this.locDist2 - d) / (this.locDist2 - this.locDist1);
      }

      // ==================== 敌人显示 ====================

      private function unitBBox(loc:Location, u:Unit):Array
      {
         // 外扩 1 瓦片（v0.21）：小体型敌人（如炮塔 phis 38×38 < 40px 瓦片）
         // 包围盒只有 1 个瓦片 → 明暗边界处瓦片级二值判定 → 全出现-全消失
         // 二分。外扩后跨边界时进入部分可见态（state=2），由子格掩膜精确
         // 裁剪（掩膜内容按子格 raycast，外扩圈只扩大候选区域，不改变可见
         // 语义）
         var x0:int = Math.floor((u.X - u.scX / 2) / Tile.tileX) - 1;
         var x1:int = Math.floor((u.X + u.scX / 2) / Tile.tileX) + 1;
         var y0:int = Math.floor((u.Y - u.scY) / Tile.tileY) - 1;
         var y1:int = Math.floor(u.Y / Tile.tileY) + 1;
         if(x0 < 0)
         {
            x0 = 0;
         }
         if(y0 < 0)
         {
            y0 = 0;
         }
         if(x1 >= this.spaceX)
         {
            x1 = this.spaceX - 1;
         }
         if(y1 >= this.spaceY)
         {
            y1 = this.spaceY - 1;
         }
         if(x1 < x0)
         {
            x1 = x0;
         }
         if(y1 < y0)
         {
            y1 = y0;
         }
         return [x0,y0,x1,y1];
      }

      private function bboxFovCount(bb:Array):int
      {
         var n:int = 0;
         var tx:int;
         var ty:int;
         for(tx = bb[0]; tx <= bb[2]; tx++)
         {
            for(ty = bb[1]; ty <= bb[3]; ty++)
            {
               // 明亮视野 + 部分透光（木门/栅格/水后）都算"可见"（暗色显示、可抓取）
               if(this.fov[tx + ty * this.spaceX] != FOV_NONE)
               {
                  n++;
               }
            }
         }
         return n;
      }

      private function bboxTotal(bb:Array):int
      {
         return (bb[2] - bb[0] + 1) * (bb[3] - bb[1] + 1);
      }

      private function enemyState(loc:Location, u:Unit):int
      {
         var bb:Array = this.unitBBox(loc,u);
         var total:int = this.bboxTotal(bb);
         var n:int = this.bboxFovCount(bb);
         if(n <= 0)
         {
            return 0;
         }
         if(n >= total)
         {
            return 1;
         }
         return 2;
      }

            /**
       * FOV 掩膜（只在部分可见时）：矢量 Shape + 模糊位图填充 + cacheAsBitmap
       * （v0.24.4——v0.24.3 补上 alpha 掩膜缺失的 cacheAsBitmap：Flash 文档
       * 明确，掩膜与被掩膜对象都须 cacheAsBitmap=true，掩膜才尊重 alpha 通道，
       * 否则按二值覆盖光栅化、位图填充内容甚至不渲染 → 二分）。
       *
       * 内容：子格二值场写入小位图 m2d、按模式模糊到 m2e（classic 6/q2≈40px
       * / current 4/q3≈32px，对齐各自雾层边界宽度），beginBitmapFill(smooth)
       * 放大绘制进 Shape → 敌人明暗交界渐变淡出，无 5px 硬阶梯颗粒。
       * 子格级 raycast + castRay 返回 -1（墙瓦片）回退 fov（墙炮塔不消失）；
       * 区域覆盖包围盒并向上/左右外扩（血条/动画）；按 FOV 版本+区域签名门控。
       */
      private function applyMask(w:World, u:Unit, bb:Array):void
      {
         var rec:Object = this.unitVis[u];
         if(rec == null)
         {
            rec = {state:1,m2:null,m3:null,m2d:null,m2e:null,lastFov:-1,lastBb:""};
            this.unitVis[u] = rec;
         }
         var x0:int = bb[0] - MASK_PAD_X;
         var y0:int = bb[1] - MASK_PAD_TOP;
         var x1:int = bb[2] + MASK_PAD_X;
         var y1:int = bb[3] + MASK_PAD_BOTTOM;
         if(x0 < 0)
         {
            x0 = 0;
         }
         if(y0 < 0)
         {
            y0 = 0;
         }
         if(x1 >= this.spaceX)
         {
            x1 = this.spaceX - 1;
         }
         if(y1 >= this.spaceY)
         {
            y1 = this.spaceY - 1;
         }
         var sig:String = x0 + "," + y0 + "," + x1 + "," + y1;
         if(rec.lastFov == this.fovVersion && rec.lastBb == sig)
         {
            return;
         }
         rec.lastFov = this.fovVersion;
         rec.lastBb = sig;
         var totx:int = (x1 - x0 + 1) * MASK_SUB;
         var toty:int = (y1 - y0 + 1) * MASK_SUB;
         var bd:BitmapData = rec.m2d as BitmapData;   // 子格二值场
         var bdb:BitmapData = rec.m2e as BitmapData;  // 模糊后显示源
         if(bd == null || bd.width != totx || bd.height != toty)
         {
            if(bd != null)
            {
               bd.dispose();
            }
            if(bdb != null)
            {
               bdb.dispose();
            }
            bd = new BitmapData(totx,toty,true,0);
            bdb = new BitmapData(totx,toty,true,0);
            rec.m2d = bd;
            rec.m2e = bdb;
         }
         else
         {
            bd.fillRect(bd.rect,0);   // 清透明（复用）
         }
         var s2:Shape = rec.m2 as Shape;
         var s3:Shape = rec.m3 as Shape;
         if(s2 == null)
         {
            s2 = new Shape();
            rec.m2 = s2;
         }
         if(s3 == null)
         {
            s3 = new Shape();
            rec.m3 = s3;
         }
         if(w.grafon != null)
         {
            if(u.vis != null)
            {
               if(s2.parent != w.grafon.visObjs[2]) { w.grafon.visObjs[2].addChild(s2); }
            }
            else if(s2.parent != null) { s2.parent.removeChild(s2); }
            if(u.hpbar != null)
            {
               if(s3.parent != w.grafon.visObjs[3]) { w.grafon.visObjs[3].addChild(s3); }
            }
            else if(s3.parent != null) { s3.parent.removeChild(s3); }
         }
         try
         {
            // v0.24.4：alpha 掩膜（软边）要求**掩膜与被掩膜对象都
            // cacheAsBitmap=true**（Flash 文档明确：否则掩膜按二值覆盖光栅化、
            // 位图填充内容甚至不渲染 → 敌人"全出现-全消失"二分——v0.24.3 即
            // 此失败）。只在本路径（state=2 部分可见）开启，clearMask 还原。
            s2.cacheAsBitmap = true;
            s3.cacheAsBitmap = true;
            if(u.vis)
            {
               u.vis.cacheAsBitmap = true;
               u.vis.mask = s2;
            }
            if(u.hpbar)
            {
               u.hpbar.cacheAsBitmap = true;
               u.hpbar.mask = s3;
            }
         }
         catch(err:Error)
         {
         }
         // 子格级判定（5px）：castRay -1（墙）回退 fov（墙炮塔不消失）
         var cs:Number = Tile.tileX / MASK_SUB;
         var scx:int;
         var scy:int;
         bd.lock();
         if(this.cfgMode == "current" && this.fogCache != null)
         {
            // v0.24.5（current）：直接采样最终雾场 fogCache（已含距离衰减/
            // 墙亮面/门景/记忆区）——零 raycast（敌人掩膜从每 FOV 变化数千
            // 次 castRay 降到数千次 getPixel32），且掩膜与雾层**像素级对齐**
            // （敌人按雾的实际渲染淡出，含衰减环/门景边界）。fogCache 与
            // 掩膜同为 8×8 子格/瓦片（FOG_SUB==MASK_SUB），索引直接换算；
            // 该路径只在 fovVersion 变化帧运行（fogCache 恰为本帧刷新）。
            var fg:BitmapData = this.fogCache;
            var a0:int;
            for(scx = 0; scx < totx; scx++)
            {
               for(scy = 0; scy < toty; scy++)
               {
                  var wx:Number = (x0 * MASK_SUB + scx + 0.5) * cs;
                  var wy:Number = (y0 * MASK_SUB + scy + 0.5) * cs;
                  var ftx:int = Math.floor(wx / Tile.tileX);
                  var fty:int = Math.floor(wy / Tile.tileY);
                  if(ftx < 0) { ftx = 0; }
                  else if(ftx >= this.spaceX) { ftx = this.spaceX - 1; }
                  if(fty < 0) { fty = 0; }
                  else if(fty >= this.spaceY) { fty = this.spaceY - 1; }
                  a0 = fg.getPixel32(FOG_PAD + ftx * FOG_SUB
                     + Math.floor((wx - ftx * Tile.tileX) / cs),
                     FOG_PAD + fty * FOG_SUB
                     + Math.floor((wy - fty * Tile.tileY) / cs)) >>> 24;
                  if(a0 < MASK_LIT_A)
                  {
                     bd.setPixel32(scx,scy,0xFFFFFFFF);
                  }
               }
            }
         }
         else if(this.cfgMode == "classic" && this.classicRaw != null)
         {
            // v0.24.7（classic）：采样雾层 classicRaw（1px/瓦片，瓦片级缓存
            // 复用）——零 raycast；掩膜与 classic 雾层**瓦片级对齐**（门景/
            // 衰减环/记忆区/墙协调值，阈值同为 MASK_LIT_A=140）
            if(this.cfgAutoTest)
            {
               this.atMaskRaw++;
            }
            var lTx:int = -1;
            var lTy:int = -1;
            var lA:int = 255;
            for(scx = 0; scx < totx; scx++)
            {
               for(scy = 0; scy < toty; scy++)
               {
                  var cwx:Number = (x0 * MASK_SUB + scx + 0.5) * cs;
                  var cwy:Number = (y0 * MASK_SUB + scy + 0.5) * cs;
                  var ctx:int = Math.floor(cwx / Tile.tileX);
                  var cty:int = Math.floor(cwy / Tile.tileY);
                  if(ctx < 0) { ctx = 0; }
                  else if(ctx >= this.spaceX) { ctx = this.spaceX - 1; }
                  if(cty < 0) { cty = 0; }
                  else if(cty >= this.spaceY) { cty = this.spaceY - 1; }
                  if(ctx != lTx || cty != lTy)
                  {
                     lA = this.classicRaw.getPixel32(ctx,cty) >>> 24;
                     lTx = ctx;
                     lTy = cty;
                  }
                  if(lA < MASK_LIT_A)
                  {
                     bd.setPixel32(scx,scy,0xFFFFFFFF);
                  }
               }
            }
         }
         else
         {
            if(this.cfgAutoTest)
            {
               this.atMaskRay++;
            }
            var d2max:Number = this.locDist2 * this.locDist2;
            for(scx = 0; scx < totx; scx++)
            {
               for(scy = 0; scy < toty; scy++)
               {
                  var swx:Number = (x0 * MASK_SUB + scx + 0.5) * cs;
                  var swy:Number = (y0 * MASK_SUB + scy + 0.5) * cs;
                  var dddx:Number = swx - this.eyeX;
                  var dddy:Number = swy - this.eyeY;
                  var lit:Number = dddx * dddx + dddy * dddy <= d2max
                     ? this.castRay(this.curLoc,this.eyeX,this.eyeY,swx,swy,
                        Math.floor(swx / Tile.tileX),Math.floor(swy / Tile.tileY))
                     : -1;
                  if(lit < 0)
                  {
                     lit = this.fov[Math.floor(swx / Tile.tileX) + Math.floor(swy / Tile.tileY) * this.spaceX] != FOV_NONE ? 1 : 0;
                  }
                  if(lit > 0.0001)
                  {
                     bd.setPixel32(scx,scy,0xFFFFFFFF);
                  }
               }
            }
         }
         bd.unlock();
         // 按模式模糊（classic/current 各自对齐雾层边界宽度）；0=关闭（硬边）
         var blur:BlurFilter = this.cfgMode == "classic" ? this.maskBlurClassic : this.maskBlurCurrent;
         if(blur.blurX > 0)
         {
            bdb.applyFilter(bd,bd.rect,this.fogPoint,blur);
         }
         else
         {
            bdb.copyPixels(bd,bd.rect,this.fogPoint);
         }
         // 位图填充绘制进矢量 Shape（smoothing → 双线性放大），alpha 渐变即软边
         // 注：beginBitmapFill 的 matrix 不跨调用复用（可能持引用，复用会串改
         // 前一个敌人的填充）——每次新建，成本可忽略（仅 FOV 变化时调用）
         var g:flash.display.Graphics = s2.graphics;
         g.clear();
         var m:Matrix = new Matrix(cs,0,0,cs,x0 * Tile.tileX,y0 * Tile.tileY);
         g.beginBitmapFill(bdb,m,false,true);
         g.drawRect(x0 * Tile.tileX,y0 * Tile.tileY,totx * cs,toty * cs);
         g.endFill();
         s3.graphics.clear();
         s3.graphics.copyFrom(g);
      }

      private function clearMask(u:Unit):void
      {
         var rec:Object = this.unitVis[u];
         if(rec == null)
         {
            return;
         }
         try
         {
            if(u.vis)
            {
               u.vis.mask = null;
               u.vis.cacheAsBitmap = false;
            }
            if(u.hpbar)
            {
               u.hpbar.mask = null;
               u.hpbar.cacheAsBitmap = false;
            }
         }
         catch(err:Error)
         {
         }
         // 掩膜必须移出图层：不被 mask 引用时会被当普通内容渲染（白块）
         var s2:Shape = rec.m2 as Shape;
         var s3:Shape = rec.m3 as Shape;
         if(s2 != null && s2.parent != null) { s2.parent.removeChild(s2); }
         if(s3 != null && s3.parent != null) { s3.parent.removeChild(s3); }
         rec.lastFov = -1;
      }

      /** 定期清扫：掩膜所属单位已死亡/摘除（vis 不再挂载）时移除残留掩膜位图。 */
      private function sweepMasks():void
      {
         for(var k:Object in this.unitVis)
         {
            var rec:Object = this.unitVis[k];
            if(rec == null)
            {
               continue;
            }
            var u:Unit = k as Unit;
            if(u == null)
            {
               continue;
            }
            if(rec.state == 2 && (u.vis == null || u.vis.parent == null))
            {
               this.clearMask(u);
               delete this.unitVis[k];   // 摘除条目：Shape+掩膜位图随回收
            }
         }
      }

      /** 敌人全隐：每帧强制压暗 vis 与 hpbar；prior 置 0 使游戏下一帧不再把
       *  其设为 celObj（名称标签/交互目标的上游来源）。 */
      private function hideUnit(u:Unit):void
      {
         this.hpHidden[u] = true;
         try
         {
            if(u.vis)
            {
               u.vis.visible = false;
            }
            if(u.hpbar)
            {
               u.hpbar.visible = false;
            }
            u.prior = 0;
         }
         catch(err:Error)
         {
         }
      }

      /** 恢复显示：hpbar 状态交给游戏 visDetails() 重算；恢复 prior 选择权重。 */
      private function showUnit(u:Unit):void
      {
         try
         {
            if(u.vis)
            {
               u.vis.visible = true;
            }
            u.prior = 1;
         }
         catch(err:Error)
         {
         }
         if(this.hpHidden[u] == true)
         {
            delete this.hpHidden[u];
            try
            {
               u.visDetails();
            }
            catch(err:Error)
            {
            }
         }
      }

      private function hideEnemies(w:World, loc:Location, needFov:Boolean):void
      {
         var gg:UnitPlayer = loc.gg;
         var hiddenPos:Array = [];
         var visiblePos:Array = [];
         var exempt:Dictionary = new Dictionary(true);
         var units:Array = loc.units;
         var k:int;
         if(this.cfgAutoTest)
         {
            this.atE0 = 0;
            this.atE1 = 0;
            this.atE2 = 0;
         }
         if(units != null)
         {
            for(k = 0; k < units.length; k++)
            {
               var u:Unit = units[k] as Unit;
               if(u == null)
               {
                  continue;
               }
               if(u.vis)
               {
                  exempt[u.vis] = true;
               }
               if(u.player || u.npc || u.fraction == Unit.F_PLAYER || u.invis)
               {
                  visiblePos.push([u.X,u.Y]);
                  continue;
               }
               var st:int = this.enemyState(loc,u);
               if(this.cfgAutoTest)
               {
                  if(st == 0)
                  {
                     this.atE0++;
                  }
                  else if(st == 1)
                  {
                     this.atE1++;
                  }
                  else
                  {
                     this.atE2++;
                  }
               }
               if(u.sost == 4)
               {
                  this.clearMask(u);
                  this.showUnit(u);
                  visiblePos.push([u.X,u.Y]);
                  continue;
               }
               // 被抓取的敌人同样遵循视野规则：拖入暗处即不可见（宽限倒计时仍在
               // enforceTele 里独立运行）
               var rec:Object = this.unitVis[u];
               if(rec == null)
               {
                  rec = {state:1,m2:null,m3:null,m2d:null,m2e:null,lastFov:-1,lastBb:""};
                  this.unitVis[u] = rec;
               }
               rec.state = st;
               if(st == 0)
               {
                  this.clearMask(u);
                  this.hideUnit(u);
                  hiddenPos.push([u.X,u.Y]);
               }
               else if(st == 1)
               {
                  this.clearMask(u);
                  this.showUnit(u);
                  visiblePos.push([u.X,u.Y]);
               }
               else
               {
                  this.showUnit(u);
                  this.applyMask(w,u,this.unitBBox(loc,u));
                  visiblePos.push([u.X,u.Y]);
               }
            }
         }
         // 敌方手持武器：跟随所属敌人的显示状态。
         // v0.24.7：扫描门控——fov 变化帧或每 3 帧（敌人在明暗边界移动时
         // 武器状态滞后 ≤3 帧 ≈50ms，不可察觉；省去每帧遍历整条对象链）
         if(needFov || this.frameCount % 3 == 0)
         {
            if(this.cfgAutoTest)
            {
               this.atWsEx++;
            }
            var obj:Pt = loc.firstObj;
            var guard:int = 0;
            while(obj != null && guard < 5000)
            {
               if(obj is Weapon)
               {
                  var wpn:Weapon = obj as Weapon;
                  if(wpn.vis)
                  {
                     exempt[wpn.vis] = true;
                  }
                  var owner:Unit = wpn.owner;
                  if(owner != null && owner != gg && !owner.player && !owner.npc && owner.fraction != Unit.F_PLAYER)
                  {
                     // 按所属敌人当前瓦片实时判定（含尸体与被抓取状态；拖入暗处武器
                     // 同样隐藏）
                     var wst:int = this.enemyState(loc,owner);
                     if(wst == 0)
                     {
                        this.setWeaponVis(wpn,false);
                     }
                     else if(wst == 2)
                     {
                        var orec2:Object = this.unitVis[owner];
                        if(wpn.vis && orec2 != null && orec2.m2 != null)
                        {
                           wpn.vis.visible = true;
                           // v0.24.6：武器挂掩膜同样必须 cacheAsBitmap=true——
                           // 否则位图填充掩膜按路径光栅化（整块矩形），贴墙敌人
                           // （bbox 含邻域点亮的墙瓦片 → state=2）在记忆区里武器
                           // 全显（本体被掩膜正确裁掉，武器却整把可见）
                           wpn.vis.cacheAsBitmap = true;
                           wpn.vis.mask = orec2.m2;
                        }
                        else
                        {
                           this.setWeaponVis(wpn,true);
                        }
                     }
                     else
                     {
                        this.setWeaponVis(wpn,true);
                     }
                  }
                  else
                  {
                     this.setWeaponVis(wpn,true);
                  }
               }
               obj = obj.nobj;
               guard++;
            }
         }
         else if(this.cfgAutoTest)
         {
            this.atWsSk++;
         }
         // 显示树扫描：隐藏未被识别的子对象（狮鹫手臂等）；无全隐敌人时提前退出
         if((needFov || this.frameCount % 3 == 0) && (hiddenPos.length > 0 || this.managedCount > 0))
         {
            this.scanArms(w,hiddenPos,visiblePos,exempt);
         }
      }

      private function setWeaponVis(wpn:Weapon, visB:Boolean):void
      {
         try
         {
            if(wpn.vis)
            {
               wpn.vis.mask = null;
               wpn.vis.cacheAsBitmap = false;   // v0.24.6：无掩膜即关缓存（防残留开销）
               wpn.vis.visible = visB;
            }
         }
         catch(err:Error)
         {
         }
      }

      private function scanArms(w:World, hiddenPos:Array, visiblePos:Array, exempt:Dictionary):void
      {
         if(w.grafon == null)
         {
            return;
         }
         var layer:Sprite = w.grafon.visObjs[2];
         var i:int;
         for(i = 0; i < layer.numChildren; i++)
         {
            var c:DisplayObject = layer.getChildAt(i);
            if(c == null || exempt[c] == true)
            {
               continue;
            }
            var nearHidden:Boolean = this.nearAny(c,hiddenPos);
            if(nearHidden && !this.nearAny(c,visiblePos))
            {
               if(c.visible)
               {
                  c.visible = false;
                  this.managedHidden[c] = true;
                  this.managedCount++;
               }
            }
            else if(this.managedHidden[c] == true)
            {
               c.visible = true;
               delete this.managedHidden[c];
               this.managedCount--;
            }
         }
      }

      private function nearAny(c:DisplayObject, pos:Array):Boolean
      {
         for each(var p:Array in pos)
         {
            var dx:Number = c.x - p[0];
            var dy:Number = c.y - p[1];
            if(dx > -ARM_SCAN_R && dx < ARM_SCAN_R && dy > -ARM_SCAN_R && dy < ARM_SCAN_R)
            {
               return true;
            }
         }
         return false;
      }

      // ==================== 念力规则 ====================

      private function enforceTele(loc:Location):void
      {
         var gg:UnitPlayer = loc.gg;
         if(gg == null)
         {
            return;
         }
         var t:* = gg.teleObj;
         if(t == null || !(t is Unit) || t === gg)
         {
            this.teleGraceFrames = 0;
            this.teleLast = null;
            return;
         }
         if(t !== this.teleLast)
         {
            this.teleLast = t;
            this.teleGraceFrames = 0;
            if(this.cfgAutoTest)
            {
               this.fileLog("auto tele grab id=" + (t as Unit).id
                  + " st=" + this.enemyState(loc,t as Unit));
            }
         }
         var u:Unit = t as Unit;
         if(u.fraction == Unit.F_PLAYER)
         {
            return;
         }
         if(this.enemyState(loc,u) == 0)
         {
            this.teleGraceFrames++;
            var max:int = this.cfgTeleGrace * World.fps;
            if(max < 1)
            {
               max = 1;
            }
            if(this.teleGraceFrames >= max)
            {
               this.teleGraceFrames = 0;
               if(this.cfgAutoTest)
               {
                  this.fileLog("auto tele expire id=" + u.id
                     + " after " + max + "f -> dropTeleObj");
               }
               gg.dropTeleObj();
            }
         }
         else
         {
            if(this.cfgAutoTest && this.teleGraceFrames > 0)
            {
               this.fileLog("auto tele release id=" + u.id
                  + " graceFrames=" + this.teleGraceFrames);
            }
            this.teleGraceFrames = 0;
         }
      }

      // ==================== 设置界面（哔哔小马选项页） ====================

      /** 渲染模式轮换（F12 与选项页注入行共用）：vanilla → classic → current。 */
      private function cycleMode():void
      {
         this.cfgMode = this.cfgMode == "vanilla" ? "classic"
            : (this.cfgMode == "classic" ? "current" : "vanilla");
         this.saveConfig();
         this.curLoc = null;
         this.errCount = 0;
         this.showToast();
         trace("[RVision] mode=" + this.cfgMode);
         if(this.cfgAutoTest)
         {
            this.fileLog("auto mode -> " + this.cfgMode);
         }
      }

      /** 模式显示名。 */
      private function modeName():String
      {
         return this.cfgMode == "vanilla" ? "原版"
            : (this.cfgMode == "classic" ? "仿原版" : "平滑阴影");
      }

      /** F12 切换时在屏幕上短暂显示当前模式（3 秒）。 */
      private function showToast():void
      {
         var w:World = World.w;
         if(w == null || w.main == null)
         {
            return;
         }
         if(this.toastTxt == null)
         {
            this.toastTxt = new TextField();
            this.toastTxt.autoSize = TextFieldAutoSize.LEFT;
            this.toastTxt.background = true;
            this.toastTxt.backgroundColor = 0;
            this.toastTxt.textColor = 0xFFFFFF;
            this.toastTxt.selectable = false;
            this.toastTxt.mouseEnabled = false;
            w.main.addChild(this.toastTxt);
         }
         this.toastTxt.text = "视野渲染模式: " + this.modeName()
            + (this.cfgEnabled ? "" : "（已停用）");
         this.toastTxt.x = (this.stageRef != null ? this.stageRef.stageWidth : 1280) - 330;
         this.toastTxt.y = 60;
         this.toastTxt.visible = true;
         this.toastFrames = 90;
      }

      /**
       * 哔哔小马选项页（fe.inter::PipPageOpt）打开时，在界面左下角显示本模组
       * 开关面板（F11 切换，与页面自身按键导航不冲突）。
       */
      private function updateOptPanel(w:World):void
      {
         var onOpt:Boolean = false;
         try
         {
            if(w.pip != null && w.pip.active && w.pip.currentPage != null
               && getQualifiedClassName(w.pip.currentPage) == "fe.inter::PipPageOpt")
            {
               onOpt = true;
            }
         }
         catch(err:Error)
         {
         }
         if(onOpt)
         {
            this.ensureOptPanel(w);
            var txt:String = "RealisticVision 视野系统: " + (this.cfgEnabled ? "开启" : "关闭")
               + "  模式: " + this.modeName()
               + (this.cfgEnabled && !w.black ? "\n（游戏黑暗选项已关闭，模组暂不生效）" : "")
               + "\nF11 开关 / F12 或点击上方列表行换模式";
            if(this.optTxt.text != txt)
            {
               this.optTxt.text = txt;
            }
            this.optPanel.visible = true;
            // v0.25.0：向选项页原生列表注入"视野渲染模式"行（点击循环）
            this.ensureOptRow(w);
            if(this.optRow != null)
            {
               // 锚点行 id=="fullscreen" 仅在系统选项子卡存在——其余子卡隐藏本行
               var tab:Boolean = this.optRowAnchor != null
                  && this.optRowAnchor.hasOwnProperty("parent")
                  && this.optRowAnchor["parent"] != null
                  && this.optRowAnchor["id"] is TextField
                  && this.optRowAnchor["id"].text == "fullscreen";
               this.optRow.visible = tab;
               if(tab)
               {
                  var numTxt:String = this.modeName() + (this.cfgEnabled ? "" : "（停用）");
                  if(this.optRow["numb"].text != numTxt)
                  {
                     this.optRow["numb"].text = numTxt;
                  }
               }
            }
         }
         else if(this.optPanel != null && this.optPanel.visible)
         {
            this.optPanel.visible = false;
            if(this.optRow != null)
            {
               this.optRow.visible = false;
            }
         }
      }

      /**
       * v0.25.0：向哔哔小马选项页（PipPageOpt）的原生选项列表注入一行
       * "视野渲染模式"，点击循环 vanilla → classic → current。
       * 做法：DFS 找到原生行（id 文本 == "fullscreen"，选项子卡的锚点行），
       * 用 Object(row).constructor 实例化同类行（原生 visPipOptItem，观感
       * 与导航样式一致），按 setStatItem(page2==3) 的填充规则隐藏 check/scr/
       * key 等子件，放到列表最后一条已填充行的下一格。任何失败静默降级
       * （左下面板与 F12 仍可用）。行不参与原生键盘导航/滚动（选项子卡
       * 15 条 < 18 行容量，无滚动），仅鼠标点击。
       */
      private function ensureOptRow(w:World):void
      {
         if(this.optRow != null && this.optRow["parent"] != null)
         {
            return;
         }
         try
         {
            var anchor:Object = this.findRowById(w.main,"fullscreen",0);
            if(anchor == null)
            {
               return;
            }
            var host:DisplayObjectContainer = anchor["parent"] as DisplayObjectContainer;
            if(host == null)
            {
               return;
            }
            var cls:Class = anchor["constructor"] as Class;
            var row:Object = new cls();
            // 填充规则照抄 PipPageOpt.setStatItem(page2==3) 的行初始化
            row["id"].visible = false;
            row["scr"].visible = false;
            row["check"].visible = false;
            row["key1"].visible = false;
            row["key2"].visible = false;
            row["ramka"].visible = false;
            row["land"].text = "";
            row["ggName"].text = "";
            row["nazv"].text = "视野渲染模式";
            row["numb"].text = this.modeName();
            // 放到列表最后一条已填充行（id 文本非空）的下一格（行距 30）
            var lastY:Number = anchor["y"];
            var cnt:int = host.numChildren;
            var ci:int;
            for(ci = 0; ci < cnt; ci++)
            {
               var sib:DisplayObject = host.getChildAt(ci);
               if(sib.hasOwnProperty("id") && sib.hasOwnProperty("nazv")
                  && sib["id"] is TextField && sib["id"].text != "")
               {
                  if(sib["y"] > lastY)
                  {
                     lastY = sib["y"];
                  }
               }
            }
            row["x"] = anchor["x"];
            row["y"] = lastY + 30;
            row["buttonMode"] = true;
            row.addEventListener(MouseEvent.CLICK,this.onOptRowClick);
            host.addChild(row as DisplayObject);
            this.optRow = row;
            this.optRowAnchor = anchor;
            this.fileLog("optRow injected y=" + row["y"]);
         }
         catch(err:Error)
         {
            this.fileLog("optRow inject failed: " + err);
            this.optRow = null;
            this.optRowAnchor = null;
         }
      }

      /** 深度优先在显示树中找带 id 文本框且文本==idStr 的行（哔哔小马行是动态 MovieClip）。 */
      private function findRowById(node:DisplayObject,idStr:String,depth:int):Object
      {
         if(node == null || depth > 10)
         {
            return null;
         }
         try
         {
            if(node.hasOwnProperty("id") && node.hasOwnProperty("nazv")
               && node["id"] is TextField && node["id"].text == idStr && node.visible)
            {
               return node;
            }
         }
         catch(err:Error)
         {
         }
         if(node is DisplayObjectContainer)
         {
            var c:int = (node as DisplayObjectContainer).numChildren;
            var i:int;
            for(i = 0; i < c; i++)
            {
               var r:Object = this.findRowById((node as DisplayObjectContainer).getChildAt(i),idStr,depth + 1);
               if(r != null)
               {
                  return r;
               }
            }
         }
         return null;
      }

      /** 点击注入行：循环渲染模式（行内文本随 updateOptPanel 刷新）。 */
      private function onOptRowClick(e:MouseEvent):void
      {
         this.cycleMode();
         if(this.optRow != null)
         {
            this.optRow["numb"].text = this.modeName() + (this.cfgEnabled ? "" : "（停用）");
         }
      }

      private function ensureOptPanel(w:World):void
      {
         if(this.optPanel != null)
         {
            return;
         }
         if(w.main == null)
         {
            return;
         }
         this.optPanel = new Sprite();
         this.optPanel.mouseEnabled = false;
         this.optPanel.mouseChildren = false;
         this.optPanel.graphics.beginFill(0x000000,0.78);
         this.optPanel.graphics.drawRect(0,0,340,52);
         this.optPanel.graphics.endFill();
         this.optTxt = new TextField();
         this.optTxt.textColor = 0xEEEEEE;
         this.optTxt.x = 10;
         this.optTxt.y = 6;
         this.optTxt.width = 320;
         this.optTxt.height = 44;
         this.optTxt.wordWrap = true;
         this.optTxt.selectable = false;
         this.optPanel.addChild(this.optTxt);
         w.main.addChild(this.optPanel);
         this.optPanel.x = 16;
         this.optPanel.y = (this.stageRef != null ? this.stageRef.stageHeight : 800) - 68;
      }

      // ==================== 调试 ====================

      private function debugStep(w:World, loc:Location, normal:Boolean):void
      {
         // v0.24.8：移除本函数原有的 frameCount++（与 onFrame 的 ++ 形成双
         // 递增）——双递增使 frameCount 每渲染帧 +2、奇偶恒定，classic 的
         // 30Hz 门控（fc&1）因此恒全开或恒全关（自动化验证实测 cls=150/0，
         // 优化失效），fov 30 帧兜底退化为每 15 帧。移除后各 %N 门槛恢复
         // 设计语义（门控真 30Hz、兜底真 30 帧、tick 真 3 秒）
         // 模式切换提示（3 秒）
         if(this.toastFrames > 0)
         {
            this.toastFrames--;
            if(this.toastFrames == 0 && this.toastTxt != null)
            {
               this.toastTxt.visible = false;
            }
         }
         if(!this.dbgOn)
         {
            if(this.dbgTxt)
            {
               this.dbgTxt.visible = false;
            }
            return;
         }
         if(this.frameCount % 15 != 0)
         {
            return;
         }
         if(this.dbgTxt == null)
         {
            if(w.main == null)
            {
               return;
            }
            this.dbgTxt = new TextField();
            this.dbgTxt.autoSize = TextFieldAutoSize.LEFT;
            this.dbgTxt.background = true;
            this.dbgTxt.backgroundColor = 0;
            this.dbgTxt.textColor = 0xEEEEEE;
            this.dbgTxt.x = 8;
            this.dbgTxt.y = 8;
            w.main.addChild(this.dbgTxt);
         }
         var msg:String = "RVision " + loc.id + " mode=" + this.modeName();
         if(normal)
         {
            msg += "\nmode=NORMAL (F11 开关 / F12 换模式)";
         }
         else
         {
            var nVis:int = 0;
            var nDim:int = 0;
            var nUnex:int = 0;
            var n:int = this.fov.length;
            var i:int;
            for(i = 0; i < n; i++)
            {
               if(this.fov[i] == FOV_VISIBLE)
               {
                  nVis++;
               }
               else if(this.explored[i] == 1)
               {
                  nDim++;
               }
               else
               {
                  nUnex++;
               }
            }
            msg += "\nvisible=" + nVis + " dim=" + nDim + " unex=" + nUnex
               + "\ngrace=" + (this.teleGraceFrames / World.fps).toFixed(1) + "s"
               + " frame=" + this.lastFrameMs + "ms"
               + "\nF10 面板 / F11 开关";
         }
         this.dbgTxt.visible = true;
         this.dbgTxt.text = msg;
      }
   }
}

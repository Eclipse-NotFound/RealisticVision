// 编译期存根：运行时经子 ApplicationDomain 解析到游戏真实类（勿随模组 SWF 发布）
package fe.unit
{
   import fe.Obj;
   import flash.display.Sprite;

   public class Unit extends Obj
   {
      public static var F_PLAYER:int;

      public var player:Boolean;
      public var npc:Boolean;
      public var fraction:int;
      public var invis:Boolean;
      public var sost:int;
      public var hpbar:Sprite;

      public function visDetails():void
      {
      }
   }
}

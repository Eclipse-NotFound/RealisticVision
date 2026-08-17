// 编译期存根：运行时经子 ApplicationDomain 解析到游戏真实类（勿随模组 SWF 发布）
package fe
{
   import fe.graph.Grafon;
   import fe.loc.Location;
   import fe.unit.Pers;
   import fe.unit.UnitPlayer;
   import flash.display.Sprite;

   public class World
   {
      public static var w:World;
      public static var fps:int;

      public var black:Boolean;
      public var allStat:int;
      public var celX:Number;
      public var celY:Number;
      public var loc:Location;
      public var gg:UnitPlayer;
      public var grafon:Grafon;
      public var pers:Pers;
      public var main:Sprite;
      public var pip:*;
   }
}

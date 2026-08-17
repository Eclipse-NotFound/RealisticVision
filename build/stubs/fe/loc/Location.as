// 编译期存根：运行时经子 ApplicationDomain 解析到游戏真实类（勿随模组 SWF 发布）
package fe.loc
{
   import fe.Pt;
   import fe.unit.UnitPlayer;

   public class Location
   {
      public var id:String;
      public var spaceX:int;
      public var spaceY:int;
      public var lDist1:Number;
      public var lDist2:int;
      public var opacWater:Number;
      public var active:Boolean;
      public var base:Boolean;
      public var black:Boolean;
      public var retDark:Boolean;
      public var isRelight:Boolean;
      public var isRebuild:Boolean;
      public var units:Array;
      public var firstObj:Pt;
      public var gg:UnitPlayer;
      public var celObj:*;

      public function getTile(param1:int, param2:int):Tile
      {
         return null;
      }
   }
}

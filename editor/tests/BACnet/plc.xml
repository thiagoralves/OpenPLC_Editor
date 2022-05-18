<?xml version='1.0' encoding='utf-8'?>
<project xmlns:ns1="http://www.plcopen.org/xml/tc6_0201" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns="http://www.plcopen.org/xml/tc6_0201">
  <fileHeader companyName="Unknown" productName="Unnamed" productVersion="1" creationDateTime="2018-07-28T02:24:08"/>
  <contentHeader name="BACnet" modificationDateTime="2018-09-26T14:00:21">
    <coordinateInfo>
      <fbd>
        <scaling x="0" y="0"/>
      </fbd>
      <ld>
        <scaling x="0" y="0"/>
      </ld>
      <sfc>
        <scaling x="0" y="0"/>
      </sfc>
    </coordinateInfo>
  </contentHeader>
  <types>
    <dataTypes/>
    <pous>
      <pou name="program0" pouType="program">
        <interface>
          <localVars>
            <variable name="EnergyCounter" address="%MD0.2.0">
              <type>
                <REAL/>
              </type>
            </variable>
            <variable name="Temperature" address="%ID0.0.0">
              <type>
                <REAL/>
              </type>
            </variable>
            <variable name="Humidity" address="%ID0.0.1">
              <type>
                <REAL/>
              </type>
            </variable>
          </localVars>
          <localVars>
            <variable name="TempSimulation">
              <type>
                <derived name="Simulator"/>
              </type>
            </variable>
            <variable name="HumiditySimulation">
              <type>
                <derived name="Simulator"/>
              </type>
            </variable>
          </localVars>
          <localVars>
            <variable name="TemperatureSetPoint" address="%QD0.1.0">
              <type>
                <REAL/>
              </type>
            </variable>
            <variable name="ControlDisable" address="%QX0.4.2">
              <type>
                <BOOL/>
              </type>
            </variable>
            <variable name="Heater" address="%IX0.3.0">
              <type>
                <BOOL/>
              </type>
            </variable>
            <variable name="Cooler" address="%IX0.3.1">
              <type>
                <BOOL/>
              </type>
            </variable>
          </localVars>
        </interface>
        <body>
          <FBD>
            <inVariable localId="1" executionOrderId="0" height="30" width="114" negated="false">
              <position x="299" y="521"/>
              <connectionPointOut>
                <relPosition x="114" y="15"/>
              </connectionPointOut>
              <expression>EnergyCounter</expression>
            </inVariable>
            <outVariable localId="2" executionOrderId="0" height="30" width="114" negated="false">
              <position x="654" y="521"/>
              <connectionPointIn>
                <relPosition x="0" y="15"/>
                <connection refLocalId="3" formalParameter="OUT">
                  <position x="654" y="536"/>
                  <position x="533" y="536"/>
                </connection>
              </connectionPointIn>
              <expression>EnergyCounter</expression>
            </outVariable>
            <block localId="3" typeName="ADD" executionOrderId="0" height="60" width="67">
              <position x="466" y="506"/>
              <inputVariables>
                <variable formalParameter="IN1">
                  <connectionPointIn>
                    <relPosition x="0" y="30"/>
                    <connection refLocalId="1">
                      <position x="466" y="536"/>
                      <position x="404" y="536"/>
                    </connection>
                  </connectionPointIn>
                </variable>
                <variable formalParameter="IN2">
                  <connectionPointIn>
                    <relPosition x="0" y="50"/>
                    <connection refLocalId="4">
                      <position x="466" y="556"/>
                      <position x="436" y="556"/>
                      <position x="436" y="585"/>
                      <position x="401" y="585"/>
                    </connection>
                  </connectionPointIn>
                </variable>
              </inputVariables>
              <inOutVariables/>
              <outputVariables>
                <variable formalParameter="OUT">
                  <connectionPointOut>
                    <relPosition x="67" y="30"/>
                  </connectionPointOut>
                </variable>
              </outputVariables>
            </block>
            <inVariable localId="4" executionOrderId="0" height="30" width="105" negated="false">
              <position x="296" y="570"/>
              <connectionPointOut>
                <relPosition x="105" y="15"/>
              </connectionPointOut>
              <expression>0.00131</expression>
            </inVariable>
            <comment localId="5" height="67" width="229">
              <position x="27" y="525"/>
              <content>
                <xhtml:p><![CDATA[Always consume some energy]]></xhtml:p>
              </content>
            </comment>
            <block localId="6" typeName="Simulator" instanceName="TempSimulation" executionOrderId="0" height="128" width="143">
              <position x="188" y="648"/>
              <inputVariables>
                <variable formalParameter="MinVal">
                  <connectionPointIn>
                    <relPosition x="0" y="38"/>
                    <connection refLocalId="8">
                      <position x="188" y="686"/>
                      <position x="138" y="686"/>
                    </connection>
                  </connectionPointIn>
                </variable>
                <variable formalParameter="MaxVal">
                  <connectionPointIn>
                    <relPosition x="0" y="74"/>
                    <connection refLocalId="9">
                      <position x="188" y="722"/>
                      <position x="138" y="722"/>
                    </connection>
                  </connectionPointIn>
                </variable>
                <variable formalParameter="PeriodSeconds">
                  <connectionPointIn>
                    <relPosition x="0" y="110"/>
                    <connection refLocalId="10">
                      <position x="188" y="758"/>
                      <position x="138" y="758"/>
                    </connection>
                  </connectionPointIn>
                </variable>
              </inputVariables>
              <inOutVariables/>
              <outputVariables>
                <variable formalParameter="Out">
                  <connectionPointOut>
                    <relPosition x="143" y="38"/>
                  </connectionPointOut>
                </variable>
              </outputVariables>
            </block>
            <outVariable localId="7" executionOrderId="0" height="30" width="98" negated="false">
              <position x="421" y="671"/>
              <connectionPointIn>
                <relPosition x="0" y="15"/>
                <connection refLocalId="6" formalParameter="Out">
                  <position x="421" y="686"/>
                  <position x="331" y="686"/>
                </connection>
              </connectionPointIn>
              <expression>Temperature</expression>
            </outVariable>
            <inVariable localId="8" executionOrderId="0" height="30" width="105" negated="false">
              <position x="33" y="671"/>
              <connectionPointOut>
                <relPosition x="105" y="15"/>
              </connectionPointOut>
              <expression>18.0</expression>
            </inVariable>
            <inVariable localId="9" executionOrderId="0" height="30" width="105" negated="false">
              <position x="33" y="707"/>
              <connectionPointOut>
                <relPosition x="105" y="15"/>
              </connectionPointOut>
              <expression>30.0</expression>
            </inVariable>
            <inVariable localId="10" executionOrderId="0" height="30" width="105" negated="false">
              <position x="33" y="743"/>
              <connectionPointOut>
                <relPosition x="105" y="15"/>
              </connectionPointOut>
              <expression>120</expression>
            </inVariable>
            <block localId="11" typeName="Simulator" instanceName="HumiditySimulation" executionOrderId="0" height="137" width="143">
              <position x="185" y="803"/>
              <inputVariables>
                <variable formalParameter="MinVal">
                  <connectionPointIn>
                    <relPosition x="0" y="39"/>
                    <connection refLocalId="13">
                      <position x="185" y="842"/>
                      <position x="135" y="842"/>
                    </connection>
                  </connectionPointIn>
                </variable>
                <variable formalParameter="MaxVal">
                  <connectionPointIn>
                    <relPosition x="0" y="78"/>
                    <connection refLocalId="14">
                      <position x="185" y="881"/>
                      <position x="135" y="881"/>
                    </connection>
                  </connectionPointIn>
                </variable>
                <variable formalParameter="PeriodSeconds">
                  <connectionPointIn>
                    <relPosition x="0" y="117"/>
                    <connection refLocalId="15">
                      <position x="185" y="920"/>
                      <position x="135" y="920"/>
                    </connection>
                  </connectionPointIn>
                </variable>
              </inputVariables>
              <inOutVariables/>
              <outputVariables>
                <variable formalParameter="Out">
                  <connectionPointOut>
                    <relPosition x="143" y="39"/>
                  </connectionPointOut>
                </variable>
              </outputVariables>
            </block>
            <outVariable localId="12" executionOrderId="0" height="30" width="111" negated="false">
              <position x="418" y="827"/>
              <connectionPointIn>
                <relPosition x="0" y="15"/>
                <connection refLocalId="11" formalParameter="Out">
                  <position x="418" y="842"/>
                  <position x="328" y="842"/>
                </connection>
              </connectionPointIn>
              <expression>Humidity</expression>
            </outVariable>
            <inVariable localId="13" executionOrderId="0" height="30" width="105" negated="false">
              <position x="30" y="827"/>
              <connectionPointOut>
                <relPosition x="105" y="15"/>
              </connectionPointOut>
              <expression>55.0</expression>
            </inVariable>
            <inVariable localId="14" executionOrderId="0" height="30" width="105" negated="false">
              <position x="30" y="866"/>
              <connectionPointOut>
                <relPosition x="105" y="15"/>
              </connectionPointOut>
              <expression>78.0</expression>
            </inVariable>
            <inVariable localId="15" executionOrderId="0" height="30" width="105" negated="false">
              <position x="30" y="905"/>
              <connectionPointOut>
                <relPosition x="105" y="15"/>
              </connectionPointOut>
              <expression>58</expression>
            </inVariable>
            <block localId="16" typeName="GT" executionOrderId="0" height="60" width="67">
              <position x="231" y="1103"/>
              <inputVariables>
                <variable formalParameter="IN1">
                  <connectionPointIn>
                    <relPosition x="0" y="30"/>
                    <connection refLocalId="18">
                      <position x="231" y="1133"/>
                      <position x="132" y="1133"/>
                    </connection>
                  </connectionPointIn>
                </variable>
                <variable formalParameter="IN2">
                  <connectionPointIn>
                    <relPosition x="0" y="50"/>
                    <connection refLocalId="22">
                      <position x="231" y="1153"/>
                      <position x="208" y="1153"/>
                      <position x="208" y="1169"/>
                      <position x="185" y="1169"/>
                    </connection>
                  </connectionPointIn>
                </variable>
              </inputVariables>
              <inOutVariables/>
              <outputVariables>
                <variable formalParameter="OUT">
                  <connectionPointOut>
                    <relPosition x="67" y="30"/>
                  </connectionPointOut>
                </variable>
              </outputVariables>
            </block>
            <inVariable localId="18" executionOrderId="0" height="30" width="98" negated="false">
              <position x="40" y="1118"/>
              <connectionPointOut>
                <relPosition x="98" y="15"/>
              </connectionPointOut>
              <expression>Temperature</expression>
            </inVariable>
            <block localId="19" typeName="AND" executionOrderId="0" height="60" width="67">
              <position x="347" y="1059"/>
              <inputVariables>
                <variable formalParameter="IN1" negated="true">
                  <connectionPointIn>
                    <relPosition x="0" y="30"/>
                    <connection refLocalId="20">
                      <position x="347" y="1089"/>
                      <position x="263" y="1089"/>
                      <position x="263" y="1074"/>
                      <position x="145" y="1074"/>
                    </connection>
                  </connectionPointIn>
                </variable>
                <variable formalParameter="IN2">
                  <connectionPointIn>
                    <relPosition x="0" y="50"/>
                    <connection refLocalId="16" formalParameter="OUT">
                      <position x="347" y="1109"/>
                      <position x="337" y="1109"/>
                      <position x="337" y="1133"/>
                      <position x="298" y="1133"/>
                    </connection>
                  </connectionPointIn>
                </variable>
              </inputVariables>
              <inOutVariables/>
              <outputVariables>
                <variable formalParameter="OUT">
                  <connectionPointOut>
                    <relPosition x="67" y="30"/>
                  </connectionPointOut>
                </variable>
              </outputVariables>
            </block>
            <inVariable localId="20" executionOrderId="0" height="30" width="122" negated="false">
              <position x="41" y="1059"/>
              <connectionPointOut>
                <relPosition x="122" y="15"/>
              </connectionPointOut>
              <expression>ControlDisable</expression>
            </inVariable>
            <outVariable localId="21" executionOrderId="0" height="30" width="92" negated="false">
              <position x="468" y="1074"/>
              <connectionPointIn>
                <relPosition x="0" y="15"/>
                <connection refLocalId="19" formalParameter="OUT">
                  <position x="468" y="1089"/>
                  <position x="414" y="1089"/>
                </connection>
              </connectionPointIn>
              <expression>Cooler</expression>
            </outVariable>
            <inVariable localId="22" executionOrderId="0" height="30" width="162" negated="false">
              <position x="39" y="1154"/>
              <connectionPointOut>
                <relPosition x="162" y="15"/>
              </connectionPointOut>
              <expression>TemperatureSetPoint</expression>
            </inVariable>
            <block localId="17" typeName="LT" executionOrderId="0" height="60" width="67">
              <position x="228" y="1278"/>
              <inputVariables>
                <variable formalParameter="IN1">
                  <connectionPointIn>
                    <relPosition x="0" y="30"/>
                    <connection refLocalId="23">
                      <position x="228" y="1308"/>
                      <position x="129" y="1308"/>
                    </connection>
                  </connectionPointIn>
                </variable>
                <variable formalParameter="IN2">
                  <connectionPointIn>
                    <relPosition x="0" y="50"/>
                    <connection refLocalId="27">
                      <position x="228" y="1328"/>
                      <position x="205" y="1328"/>
                      <position x="205" y="1344"/>
                      <position x="182" y="1344"/>
                    </connection>
                  </connectionPointIn>
                </variable>
              </inputVariables>
              <inOutVariables/>
              <outputVariables>
                <variable formalParameter="OUT">
                  <connectionPointOut>
                    <relPosition x="67" y="30"/>
                  </connectionPointOut>
                </variable>
              </outputVariables>
            </block>
            <inVariable localId="23" executionOrderId="0" height="30" width="98" negated="false">
              <position x="37" y="1293"/>
              <connectionPointOut>
                <relPosition x="98" y="15"/>
              </connectionPointOut>
              <expression>Temperature</expression>
            </inVariable>
            <block localId="24" typeName="AND" executionOrderId="0" height="60" width="67">
              <position x="344" y="1234"/>
              <inputVariables>
                <variable formalParameter="IN1" negated="true">
                  <connectionPointIn>
                    <relPosition x="0" y="30"/>
                    <connection refLocalId="25">
                      <position x="344" y="1264"/>
                      <position x="260" y="1264"/>
                      <position x="260" y="1249"/>
                      <position x="142" y="1249"/>
                    </connection>
                  </connectionPointIn>
                </variable>
                <variable formalParameter="IN2">
                  <connectionPointIn>
                    <relPosition x="0" y="50"/>
                    <connection refLocalId="17" formalParameter="OUT">
                      <position x="344" y="1284"/>
                      <position x="334" y="1284"/>
                      <position x="334" y="1308"/>
                      <position x="295" y="1308"/>
                    </connection>
                  </connectionPointIn>
                </variable>
              </inputVariables>
              <inOutVariables/>
              <outputVariables>
                <variable formalParameter="OUT">
                  <connectionPointOut>
                    <relPosition x="67" y="30"/>
                  </connectionPointOut>
                </variable>
              </outputVariables>
            </block>
            <inVariable localId="25" executionOrderId="0" height="30" width="122" negated="false">
              <position x="38" y="1234"/>
              <connectionPointOut>
                <relPosition x="122" y="15"/>
              </connectionPointOut>
              <expression>ControlDisable</expression>
            </inVariable>
            <outVariable localId="26" executionOrderId="0" height="30" width="92" negated="false">
              <position x="465" y="1249"/>
              <connectionPointIn>
                <relPosition x="0" y="15"/>
                <connection refLocalId="24" formalParameter="OUT">
                  <position x="465" y="1264"/>
                  <position x="411" y="1264"/>
                </connection>
              </connectionPointIn>
              <expression>Heater</expression>
            </outVariable>
            <inVariable localId="27" executionOrderId="0" height="30" width="162" negated="false">
              <position x="36" y="1329"/>
              <connectionPointOut>
                <relPosition x="162" y="15"/>
              </connectionPointOut>
              <expression>TemperatureSetPoint</expression>
            </inVariable>
            <comment localId="28" height="67" width="229">
              <position x="343" y="734"/>
              <content>
                <xhtml:p><![CDATA[Simple sensor simulation]]></xhtml:p>
              </content>
            </comment>
            <comment localId="29" height="67" width="229">
              <position x="37" y="978"/>
              <content>
                <xhtml:p><![CDATA[Climate control]]></xhtml:p>
              </content>
            </comment>
            <comment localId="30" height="464" width="773">
              <position x="14" y="16"/>
              <content>
                <xhtml:p><![CDATA[This examples shows how to work with BACnet extension.

Extensions requires native BACnet stack to be installed nearby Beremiz.
Following directory structure is expected:
<Parent directory>
  "beremiz"
  "BACnet"

If library is installed elsewhere, then place corresponding paths
in CFLAGS/LDFLAGS in project settings.

For GNU/Linux to install BACnet library in parent directory run following commands:
$ svn checkout https://svn.code.sf.net/p/bacnet/code/trunk/bacnet-stack/ BACnet
$ cd BACnet
$ make

After that BACnet extension is ready to be used in Beremiz projects.
BACnet stack implementation contains a lot of test tools. They could be useful during 
debugging and BACnet investigation. See "BACnet/bin/readme.txt" for more information about them.]]></xhtml:p>
              </content>
            </comment>
          </FBD>
        </body>
      </pou>
      <pou name="Simulator" pouType="functionBlock">
        <interface>
          <outputVars>
            <variable name="Out">
              <type>
                <REAL/>
              </type>
            </variable>
          </outputVars>
          <inputVars>
            <variable name="MinVal">
              <type>
                <REAL/>
              </type>
            </variable>
            <variable name="MaxVal">
              <type>
                <REAL/>
              </type>
            </variable>
            <variable name="PeriodSeconds">
              <type>
                <INT/>
              </type>
            </variable>
          </inputVars>
          <localVars>
            <variable name="TON0">
              <type>
                <derived name="TON"/>
              </type>
            </variable>
            <variable name="seconds">
              <type>
                <INT/>
              </type>
            </variable>
            <variable name="BaseVal">
              <type>
                <REAL/>
              </type>
            </variable>
            <variable name="VarVal">
              <type>
                <REAL/>
              </type>
            </variable>
          </localVars>
        </interface>
        <body>
          <ST>
            <xhtml:p><![CDATA[(* pseudo-random variations *)
TON0(IN := TRUE, PT := T#3120s);
IF TON0.Q THEN
  TON0(IN := FALSE);
END_IF;
seconds := TIME_TO_INT(TON0.ET);

BaseVal := (MaxVal + MinVal)/2.0;
VarVal  := (MaxVal-MinVal)*INT_TO_REAL((seconds MOD PeriodSeconds) - (PeriodSeconds/2))/INT_TO_REAL(PeriodSeconds);

Out :=  BaseVal + VarVal;]]></xhtml:p>
          </ST>
        </body>
      </pou>
    </pous>
  </types>
  <instances>
    <configurations>
      <configuration name="config">
        <resource name="resource1">
          <task name="task0" priority="0" interval="T#20ms">
            <pouInstance name="instance0" typeName="program0"/>
          </task>
        </resource>
      </configuration>
    </configurations>
  </instances>
</project>

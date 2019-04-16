<?xml version="1.0"?>
<xsl:stylesheet xmlns:exsl="http://exslt.org/common" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:ppx="http://www.plcopen.org/xml/tc6_0201" xmlns:ns="beremiz" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" extension-element-prefixes="ns" version="1.0" exclude-result-prefixes="ns">
  <xsl:output method="xml"/>
  <xsl:param name="tree"/>
  <xsl:template match="text()"/>
  <xsl:variable name="project" select="ns:GetProject()"/>
  <xsl:variable name="stdlib" select="ns:GetStdLibs()"/>
  <xsl:variable name="extensions" select="ns:GetExtensions()"/>
  <xsl:variable name="all_types" select="($project | $stdlib | $extensions)/ppx:types"/>
  <xsl:template match="ppx:configuration">
    <xsl:apply-templates select="ppx:globalVars"/>
  </xsl:template>
  <xsl:template match="ppx:resource">
    <xsl:apply-templates select="ppx:globalVars"/>
  </xsl:template>
  <xsl:template match="ppx:pou">
    <xsl:apply-templates select="ppx:interface/*"/>
  </xsl:template>
  <xsl:template match="ppx:returnType">
    <xsl:value-of select="ns:AddTree()"/>
    <xsl:apply-templates mode="var_type" select="."/>
  </xsl:template>
  <xsl:template name="variables_infos">
    <xsl:param name="var_class"/>
    <xsl:variable name="var_option">
      <xsl:choose>
        <xsl:when test="@constant='true' or @constant='1'">
          <xsl:text>Constant</xsl:text>
        </xsl:when>
        <xsl:when test="@retain='true' or @retain='1'">
          <xsl:text>Retain</xsl:text>
        </xsl:when>
        <xsl:when test="@nonretain='true' or @nonretain='1'">
          <xsl:text>Non-Retain</xsl:text>
        </xsl:when>
      </xsl:choose>
    </xsl:variable>
    <xsl:for-each select="ppx:variable">
      <xsl:variable name="initial_value">
        <xsl:apply-templates select="ppx:initialValue"/>
      </xsl:variable>
      <xsl:variable name="edit">
        <xsl:choose>
          <xsl:when test="$var_class='Global' or $var_class='External'">
            <xsl:text>true</xsl:text>
          </xsl:when>
          <xsl:otherwise>
            <xsl:apply-templates mode="var_edit" select="ppx:type"/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:variable>
      <xsl:value-of select="ns:AddTree()"/>
      <xsl:apply-templates mode="var_type" select="ppx:type"/>
      <xsl:value-of select="ns:AddVariable(@name, $var_class, $var_option, @address, $initial_value, $edit, ppx:documentation/xhtml:p/text())"/>
    </xsl:for-each>
  </xsl:template>
  <xsl:template match="ppx:localVars">
    <xsl:call-template name="variables_infos">
      <xsl:with-param name="var_class">
        <xsl:text>Local</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>
  <xsl:template match="ppx:globalVars">
    <xsl:call-template name="variables_infos">
      <xsl:with-param name="var_class">
        <xsl:text>Global</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>
  <xsl:template match="ppx:externalVars">
    <xsl:call-template name="variables_infos">
      <xsl:with-param name="var_class">
        <xsl:text>External</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>
  <xsl:template match="ppx:tempVars">
    <xsl:call-template name="variables_infos">
      <xsl:with-param name="var_class">
        <xsl:text>Temp</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>
  <xsl:template match="ppx:inputVars">
    <xsl:call-template name="variables_infos">
      <xsl:with-param name="var_class">
        <xsl:text>Input</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>
  <xsl:template match="ppx:outputVars">
    <xsl:call-template name="variables_infos">
      <xsl:with-param name="var_class">
        <xsl:text>Output</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>
  <xsl:template match="ppx:inOutVars">
    <xsl:call-template name="variables_infos">
      <xsl:with-param name="var_class">
        <xsl:text>InOut</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>
  <xsl:template mode="var_type" match="ppx:pou">
    <xsl:apply-templates mode="var_type" select="ppx:interface/*[self::ppx:inputVars or self::ppx:inOutVars or self::ppx:outputVars]/ppx:variable"/>
  </xsl:template>
  <xsl:template mode="var_type" match="ppx:variable">
    <xsl:variable name="name">
      <xsl:value-of select="@name"/>
    </xsl:variable>
    <xsl:value-of select="ns:AddTree()"/>
    <xsl:apply-templates mode="var_type" select="ppx:type"/>
    <xsl:value-of select="ns:AddVarToTree($name)"/>
  </xsl:template>
  <xsl:template mode="var_type" match="ppx:dataType">
    <xsl:apply-templates mode="var_type" select="ppx:baseType"/>
  </xsl:template>
  <xsl:template mode="var_type" match="*[self::ppx:type or self::ppx:baseType or self::ppx:returnType]/ppx:struct">
    <xsl:apply-templates mode="var_type" select="ppx:variable"/>
  </xsl:template>
  <xsl:template mode="var_type" match="*[self::ppx:type or self::ppx:baseType or self::ppx:returnType]/ppx:derived">
    <xsl:variable name="type_name">
      <xsl:value-of select="@name"/>
    </xsl:variable>
    <xsl:choose>
      <xsl:when test="$tree='True'">
        <xsl:apply-templates mode="var_type" select="$all_types/ppx:pous/ppx:pou[@name=$type_name] |                          $all_types/ppx:dataTypes/ppx:dataType[@name=$type_name]"/>
      </xsl:when>
    </xsl:choose>
    <xsl:value-of select="ns:SetType($type_name)"/>
  </xsl:template>
  <xsl:template mode="var_type" match="*[self::ppx:type or self::ppx:baseType or self::ppx:returnType]/ppx:array">
    <xsl:apply-templates mode="var_type" select="ppx:baseType"/>
    <xsl:for-each select="ppx:dimension">
      <xsl:variable name="lower">
        <xsl:value-of select="@lower"/>
      </xsl:variable>
      <xsl:variable name="upper">
        <xsl:value-of select="@upper"/>
      </xsl:variable>
      <xsl:value-of select="ns:AddDimension($lower, $upper)"/>
    </xsl:for-each>
  </xsl:template>
  <xsl:template mode="var_type" match="*[self::ppx:type or self::ppx:baseType or self::ppx:returnType]/ppx:string">
    <xsl:variable name="name">
      <xsl:text>STRING</xsl:text>
    </xsl:variable>
    <xsl:value-of select="ns:SetType($name)"/>
  </xsl:template>
  <xsl:template mode="var_type" match="*[self::ppx:type or self::ppx:baseType or self::ppx:returnType]/ppx:wstring">
    <xsl:variable name="name">
      <xsl:text>WSTRING</xsl:text>
    </xsl:variable>
    <xsl:value-of select="ns:SetType($name)"/>
  </xsl:template>
  <xsl:template mode="var_type" match="*[self::ppx:type or self::ppx:baseType or self::ppx:returnType]/*">
    <xsl:variable name="name">
      <xsl:value-of select="local-name()"/>
    </xsl:variable>
    <xsl:value-of select="ns:SetType($name)"/>
  </xsl:template>
  <xsl:template mode="var_edit" match="*[self::ppx:type or self::ppx:baseType or self::ppx:returnType]/ppx:derived">
    <xsl:variable name="type_name">
      <xsl:value-of select="@name"/>
    </xsl:variable>
    <xsl:variable name="pou_infos" select="$all_types/ppx:pous/ppx:pou[@name=$type_name]"/>
    <xsl:choose>
      <xsl:when test="$pou_infos != ''">
        <xsl:text>false</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>true</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  <xsl:template mode="var_edit" match="*[self::ppx:type or self::ppx:baseType or self::ppx:returnType]/*">
    <xsl:text>true</xsl:text>
  </xsl:template>
  <xsl:template match="ppx:value">
    <xsl:choose>
      <xsl:when test="@repetitionValue">
        <xsl:value-of select="@repetitionValue"/>
        <xsl:text>(</xsl:text>
        <xsl:apply-templates/>
        <xsl:text>)</xsl:text>
      </xsl:when>
      <xsl:when test="@member">
        <xsl:value-of select="@member"/>
        <xsl:text> := </xsl:text>
        <xsl:apply-templates/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  <xsl:template match="ppx:simpleValue">
    <xsl:value-of select="@value"/>
  </xsl:template>
  <xsl:template name="complex_type_value">
    <xsl:param name="start_bracket"/>
    <xsl:param name="end_bracket"/>
    <xsl:value-of select="$start_bracket"/>
    <xsl:for-each select="ppx:value">
      <xsl:apply-templates select="."/>
      <xsl:choose>
        <xsl:when test="position()!=last()">
          <xsl:text>, </xsl:text>
        </xsl:when>
      </xsl:choose>
    </xsl:for-each>
    <xsl:value-of select="$end_bracket"/>
  </xsl:template>
  <xsl:template match="ppx:arrayValue">
    <xsl:call-template name="complex_type_value">
      <xsl:with-param name="start_bracket">
        <xsl:text>[</xsl:text>
      </xsl:with-param>
      <xsl:with-param name="end_bracket">
        <xsl:text>]</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>
  <xsl:template match="ppx:structValue">
    <xsl:call-template name="complex_type_value">
      <xsl:with-param name="start_bracket">
        <xsl:text>(</xsl:text>
      </xsl:with-param>
      <xsl:with-param name="end_bracket">
        <xsl:text>)</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>
</xsl:stylesheet>
